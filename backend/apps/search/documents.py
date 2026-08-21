from typing import Any

from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from apps.comments.models import Comment

INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "text": {"type": "text"},
            "username": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "contains": {"type": "wildcard"},
                },
            },
            "email": {
                "type": "keyword",
                "fields": {"contains": {"type": "wildcard"}},
            },
            "created_at": {"type": "date"},
            "root_id": {"type": "keyword"},
        }
    }
}


def client() -> Elasticsearch:
    return Elasticsearch(
        settings.ELASTICSEARCH_URL,
        request_timeout=settings.ELASTICSEARCH_REQUEST_TIMEOUT_SECONDS,
    )


def ensure_index(instance: Elasticsearch | None = None) -> None:
    instance = instance or client()
    if not instance.indices.exists(index=settings.ELASTICSEARCH_INDEX):
        instance.indices.create(
            index=settings.ELASTICSEARCH_INDEX,
            mappings=INDEX_MAPPING["mappings"],
        )


def comment_document(comment: Comment) -> dict[str, Any]:
    return {
        "text": comment.search_text,
        "username": comment.author_name,
        "email": comment.author_email,
        "created_at": comment.created_at.isoformat(),
        "root_id": str(comment.root_id or comment.id),
    }


def index_comment(comment_id: str, instance: Elasticsearch | None = None) -> None:
    comment = Comment.objects.get(id=comment_id)
    instance = instance or client()
    ensure_index(instance)
    instance.index(
        index=settings.ELASTICSEARCH_INDEX,
        id=str(comment.id),
        document=comment_document(comment),
        refresh=False,
    )


def rebuild_index(instance: Elasticsearch | None = None, *, chunk_size: int = 1_000) -> int:
    instance = instance or client()
    instance.indices.delete(index=settings.ELASTICSEARCH_INDEX, ignore_unavailable=True)
    instance.indices.create(
        index=settings.ELASTICSEARCH_INDEX,
        mappings=INDEX_MAPPING["mappings"],
    )
    comments = Comment.objects.only(
        "id",
        "search_text",
        "author_name",
        "author_email",
        "created_at",
        "root_id",
    ).iterator(chunk_size=chunk_size)
    actions = (
        {
            "_index": settings.ELASTICSEARCH_INDEX,
            "_id": str(comment.id),
            "_source": comment_document(comment),
        }
        for comment in comments
    )
    indexed, _ = bulk(instance, actions, chunk_size=chunk_size)
    instance.indices.refresh(index=settings.ELASTICSEARCH_INDEX)
    return indexed
