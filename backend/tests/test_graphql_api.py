import uuid

import pytest
from apps.comments.models import Comment
from apps.graphql_api.loaders import BranchKey, _load_branches_sync
from apps.graphql_api.schema import schema
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext


def _root(name: str) -> Comment:
    comment = Comment.objects.create(
        author_name=name,
        author_email=f"{name.lower()}@example.com",
        html_text=f"<strong>{name}</strong>",
        search_text=name,
        depth=0,
    )
    comment.root_id = comment.id
    comment.save(update_fields=["root"])
    return comment


@pytest.mark.django_db(transaction=True)
def test_graphql_returns_multiple_comment_branches():
    first = _root("First")
    second = _root("Second")
    Comment.objects.create(
        author_name="Reply",
        author_email="reply@example.com",
        html_text="Reply",
        search_text="Reply",
        parent=first,
        root=first,
        depth=1,
    )

    response = Client().post(
        "/graphql",
        data={
            "query": """
                query Branches($ids: [ID!]!) {
                  commentBranches(ids: $ids, depth: 2) {
                    id
                    author { name email }
                    attachments { id originalName contentUrl }
                    replies { id text }
                  }
                }
            """,
            "variables": {"ids": [str(first.id), str(second.id)]},
        },
        content_type="application/json",
    )

    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body
    branches = body["data"]["commentBranches"]
    assert [branch["author"]["name"] for branch in branches] == ["First", "Second"]
    assert branches[0]["replies"][0]["text"] == "Reply"


@pytest.mark.django_db
def test_graphql_branch_loader_batches_database_queries():
    roots = [_root("Alpha"), _root("Beta")]
    keys = [BranchKey(comment_id=root.id, depth=2) for root in roots]

    with CaptureQueriesContext(connection) as queries:
        branches = _load_branches_sync(keys)

    assert len(queries) <= 4
    assert [branch.author.name for branch in branches if branch] == ["Alpha", "Beta"]


def test_graphql_is_read_only_and_rejects_invalid_ids():
    assert schema.schema_converter.type_map.get("Mutation") is None

    response = Client().post(
        "/graphql",
        data={"query": '{ commentBranch(id: "not-a-uuid") { id } }'},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["data"]["commentBranch"] is None
    assert response.json()["errors"][0]["message"] == "comment ID must be a UUID"


def test_graphql_limits_branch_count():
    ids = [str(uuid.uuid4()) for _ in range(26)]
    response = Client().post(
        "/graphql",
        data={
            "query": "query($ids: [ID!]!) { commentBranches(ids: $ids) { id } }",
            "variables": {"ids": ids},
        },
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["errors"][0]["message"] == "at most 25 branches can be requested"
