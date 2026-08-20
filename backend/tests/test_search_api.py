import uuid
from unittest.mock import Mock, patch

import pytest
from apps.comments.models import Comment
from apps.search.documents import rebuild_index
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_search_falls_back_to_postgresql_when_elasticsearch_is_unavailable():
    comment = Comment.objects.create(
        author_name="SearchAuthor",
        author_email="search@example.com",
        html_text="Needle in a thread",
        search_text="Needle in a thread",
        depth=0,
    )
    comment.root_id = comment.id
    comment.save(update_fields=["root"])
    elasticsearch = Mock()
    elasticsearch.search.side_effect = OSError("unavailable")
    with patch("apps.search.services.client", return_value=elasticsearch):
        response = APIClient().get("/api/search?q=Needle&sort=date&direction=asc")
    assert response.status_code == 200
    assert response.json()["source"] == "postgresql"
    assert response.json()["results"][0]["id"] == str(comment.id)


@pytest.mark.django_db
def test_search_returns_elasticsearch_results_with_highlights():
    comment_id = str(uuid.uuid4())
    root_id = str(uuid.uuid4())
    elasticsearch = Mock()
    elasticsearch.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_id": comment_id,
                    "_source": {
                        "text": "WebSocket delivery",
                        "username": "SearchAuthor",
                        "email": "search@example.com",
                        "root_id": root_id,
                        "created_at": "2026-08-20T12:00:00+00:00",
                    },
                    "highlight": {"text": ["<em>WebSocket</em> delivery"]},
                }
            ]
        }
    }

    with patch("apps.search.services.client", return_value=elasticsearch):
        response = APIClient().get("/api/search?q=websock")

    assert response.status_code == 200
    assert response.json()["source"] == "elasticsearch"
    assert response.json()["results"][0]["highlights"] == ["WebSocket delivery"]
    query = elasticsearch.search.call_args.kwargs["query"]
    assert query["bool"]["must"][0]["bool"]["should"][1]["multi_match"]["type"] == "phrase_prefix"


@pytest.mark.django_db
def test_search_rebuild_uses_bulk_streaming_for_all_comments():
    comments = []
    for index in range(3):
        comment = Comment.objects.create(
            author_name=f"Author{index}",
            author_email=f"author{index}@example.com",
            html_text=f"Comment {index}",
            search_text=f"Comment {index}",
            depth=0,
        )
        comment.root_id = comment.id
        comment.save(update_fields=["root"])
        comments.append(comment)

    elasticsearch = Mock()

    def consume_actions(instance, actions, *, chunk_size):
        documents = list(actions)
        assert instance is elasticsearch
        assert chunk_size == 2
        assert {item["_id"] for item in documents} == {str(comment.id) for comment in comments}
        return len(documents), []

    with patch("apps.search.documents.bulk", side_effect=consume_actions) as bulk_index:
        indexed = rebuild_index(elasticsearch, chunk_size=2)

    assert indexed == 3
    assert bulk_index.call_count == 1
    elasticsearch.indices.delete.assert_called_once()
    elasticsearch.indices.create.assert_called_once()
    elasticsearch.indices.refresh.assert_called_once()


def test_search_rebuild_rejects_non_positive_batch_size():
    with pytest.raises(CommandError, match="--batch-size must be positive"):
        call_command("rebuild_search_index", batch_size=0)
