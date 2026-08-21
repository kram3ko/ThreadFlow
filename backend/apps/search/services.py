import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from django.conf import settings
from django.db.models import Q
from elasticsearch import ApiError
from elasticsearch import ConnectionError as ElasticsearchConnectionError

from apps.comments.models import Comment
from apps.search.documents import client


@dataclass(frozen=True, slots=True)
class SearchResult:
    id: str
    text: str
    author_name: str
    author_email: str
    root_id: str
    created_at: str
    highlights: list[str]


def _safe_highlights(values: list[str]) -> list[str]:
    return [re.sub(r"</?em>", "", value) for value in values]


def _contains_pattern(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("*", "\\*").replace("?", "\\?")
    return f"*{escaped}*"


def _postgres_search(
    *,
    query: str,
    author: str,
    date_from: datetime | None,
    date_to: datetime | None,
    direction: str,
    limit: int,
    offset: int,
) -> tuple[list[SearchResult], int | None]:
    queryset = Comment.objects.all()
    if query:
        queryset = queryset.filter(
            Q(search_text__icontains=query) | Q(author_name__icontains=query)
        )
    if author:
        queryset = queryset.filter(
            Q(author_name__icontains=author) | Q(author_email__icontains=author)
        )
    if date_from:
        queryset = queryset.filter(created_at__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__lte=date_to)
    page = list(
        queryset.order_by(
            "created_at" if direction == "asc" else "-created_at",
            "id" if direction == "asc" else "-id",
        )[offset : offset + limit + 1]
    )
    results = [
        SearchResult(
            id=str(item.id),
            text=item.search_text,
            author_name=item.author_name,
            author_email=item.author_email,
            root_id=str(item.root_id or item.id),
            created_at=item.created_at.isoformat(),
            highlights=[item.search_text],
        )
        for item in page[:limit]
    ]
    next_offset = offset + limit if len(page) > limit else None
    return results, next_offset


def search_comments(
    *,
    query: str,
    author: str = "",
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort: str = "relevance",
    direction: str = "desc",
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[SearchResult], str, int | None]:
    """Search comments in Elasticsearch, falling back to PostgreSQL on failure.

    The query combines whole-token matching with typo tolerance and a
    phrase_prefix clause so a partial last word ("websock") also matches longer
    tokens ("websocket").
    """
    must: list[dict[str, Any]] = []
    filters: list[dict[str, Any]] = []
    if query:
        must.append(
            {
                "bool": {
                    "minimum_should_match": 1,
                    "should": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["text^2", "username", "email"],
                                "fuzziness": "AUTO",
                            }
                        },
                        {
                            "multi_match": {
                                "query": query,
                                "type": "phrase_prefix",
                                "fields": ["text^2", "username"],
                            }
                        },
                    ],
                }
            }
        )
    if author:
        pattern = _contains_pattern(author)
        must.append(
            {
                "bool": {
                    "minimum_should_match": 1,
                    "should": [
                        {
                            "wildcard": {
                                "username.contains": {
                                    "value": pattern,
                                    "case_insensitive": True,
                                }
                            }
                        },
                        {
                            "wildcard": {
                                "email.contains": {
                                    "value": pattern,
                                    "case_insensitive": True,
                                }
                            }
                        },
                    ],
                }
            }
        )
    date_range = {
        key: value.isoformat() for key, value in (("gte", date_from), ("lte", date_to)) if value
    }
    if date_range:
        filters.append({"range": {"created_at": date_range}})
    body = {
        "query": {"bool": {"must": must or [{"match_all": {}}], "filter": filters}},
        "sort": (
            [{"created_at": direction}, "_score"]
            if sort == "date"
            else ["_score", {"created_at": direction}]
        ),
        "highlight": {"fields": {"text": {}, "username": {}}},
        "size": limit + 1,
        "from_": offset,
    }
    try:
        response = client().search(index=settings.ELASTICSEARCH_INDEX, **body)
    except ApiError, ElasticsearchConnectionError, OSError:
        fallback, next_offset = _postgres_search(
            query=query,
            author=author,
            date_from=date_from,
            date_to=date_to,
            direction=direction,
            limit=limit,
            offset=offset,
        )
        return fallback, "postgresql", next_offset
    results = []
    hits = response["hits"]["hits"]
    for hit in hits[:limit]:
        source = hit["_source"]
        highlights = _safe_highlights(hit.get("highlight", {}).get("text", [source["text"]]))
        results.append(
            SearchResult(
                id=hit["_id"],
                text=source["text"],
                author_name=source["username"],
                author_email=source["email"],
                root_id=source["root_id"],
                created_at=source["created_at"],
                highlights=highlights,
            )
        )
    next_offset = offset + limit if len(hits) > limit else None
    return results, "elasticsearch", next_offset
