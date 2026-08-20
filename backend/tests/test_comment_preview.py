import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_preview_returns_sanitized_html():
    response = APIClient().post(
        "/api/comments/preview",
        {"text": "Hello <strong>world</strong><script>alert(1)</script>"},
        format="json",
    )
    assert response.status_code == 200
    html = response.json()["html"]
    assert "<strong>world</strong>" in html
    assert "<script>" not in html


@pytest.mark.django_db
def test_preview_opens_links_in_new_tab():
    response = APIClient().post(
        "/api/comments/preview",
        {"text": '<a href="https://example.com">site</a>'},
        format="json",
    )
    html = response.json()["html"]
    assert 'target="_blank"' in html
    assert "noopener" in html


@pytest.mark.django_db
def test_preview_rejects_unclosed_tags():
    response = APIClient().post(
        "/api/comments/preview",
        {"text": "Broken <strong>markup"},
        format="json",
    )
    assert response.status_code == 400
