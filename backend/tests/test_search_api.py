from unittest.mock import Mock, patch

import pytest
from apps.comments.models import Comment
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
