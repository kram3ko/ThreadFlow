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
        "/api/auth/csrf",
        "/api/auth/login",
        "/api/auth/logout",
        "/api/auth/me",
        "/api/auth/refresh",
        "/api/auth/register",
        "/api/captcha",
        "/api/comments",
        "/api/comments/{id}",
        "/api/comments/{id}/replies",
        "/api/health",
    }
    assert set(paths["/api/comments"]) == {"get", "post"}
    assert set(paths["/api/comments/{id}"]) == {"get"}
    assert set(paths["/api/comments/{id}/replies"]) == {"post"}


def test_api_documentation_pages_are_available(api_client):
    swagger_response = api_client.get("/api/docs")
    swagger_script_response = api_client.get("/api/docs?script=")
    redoc_response = api_client.get("/api/redoc")

    assert swagger_response.status_code == 200
    assert swagger_script_response.status_code == 200
    assert redoc_response.status_code == 200
    swagger_html = swagger_response.content.decode()
    redoc_html = redoc_response.content.decode()
    assert "cdn.jsdelivr.net" not in swagger_html
    assert "/static/drf_spectacular_sidecar/" in swagger_html
    assert "<script>" not in swagger_html
    assert swagger_script_response["Content-Type"].startswith("application/javascript")
    assert "script-src 'self'" in swagger_response["Content-Security-Policy"]
    assert "style-src 'self' 'unsafe-inline'" in swagger_response["Content-Security-Policy"]
    assert "cdn.jsdelivr.net" not in redoc_html
    assert "/static/drf_spectacular_sidecar/" in redoc_html
