import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


def test_openapi_schema_documents_current_routes(api_client):
    response = api_client.get("/api/schema?format=json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert set(paths) == {
        "/api/comments",
        "/api/comments/{id}",
        "/api/comments/{id}/replies",
        "/api/health",
    }
    assert set(paths["/api/comments"]) == {"get", "post"}
    assert set(paths["/api/comments/{id}"]) == {"get"}
    assert set(paths["/api/comments/{id}/replies"]) == {"post"}


def test_api_documentation_pages_are_available(api_client):
    assert api_client.get("/api/docs").status_code == 200
    assert api_client.get("/api/redoc").status_code == 200
