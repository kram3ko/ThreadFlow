import pytest
from apps.captcha.services import issue_challenge
from django.conf import settings
from rest_framework.test import APIClient


@pytest.fixture
def csrf_client() -> APIClient:
    client = APIClient(enforce_csrf_checks=True)
    response = client.get("/api/auth/csrf")
    assert response.status_code == 200
    client.credentials(HTTP_X_CSRFTOKEN=response.json()["csrf_token"])
    return client


def registration_payload() -> dict[str, str]:
    return {
        "username": "Alice",
        "email": "alice@example.com",
        "password": "Correct-Horse-Battery-Staple-47",
    }


@pytest.mark.django_db
def test_registration_sets_http_only_tokens_and_authenticates_me(csrf_client: APIClient) -> None:
    response = csrf_client.post("/api/auth/register", registration_payload(), format="json")

    assert response.status_code == 201
    assert response.json()["username"] == "Alice"
    assert response.cookies[settings.ACCESS_COOKIE_NAME]["httponly"] is True
    assert response.cookies[settings.ACCESS_COOKIE_NAME]["samesite"] == "Lax"
    assert response.cookies[settings.REFRESH_COOKIE_NAME]["httponly"] is True
    assert response.cookies[settings.REFRESH_COOKIE_NAME]["path"] == "/api/auth"

    me_response = csrf_client.get("/api/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "alice@example.com"


@pytest.mark.django_db
def test_registration_requires_csrf() -> None:
    client = APIClient(enforce_csrf_checks=True)

    response = client.post("/api/auth/register", registration_payload(), format="json")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "csrf_failed"


@pytest.mark.django_db
def test_login_rejects_invalid_credentials(csrf_client: APIClient) -> None:
    response = csrf_client.post(
        "/api/auth/login",
        {"username": "missing", "password": "Incorrect-password-47"},
        format="json",
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


@pytest.mark.django_db
def test_refresh_rotates_tokens(csrf_client: APIClient) -> None:
    register_response = csrf_client.post(
        "/api/auth/register",
        registration_payload(),
        format="json",
    )
    original_refresh = register_response.cookies[settings.REFRESH_COOKIE_NAME].value
    del csrf_client.cookies[settings.ACCESS_COOKIE_NAME]

    response = csrf_client.post("/api/auth/refresh")

    assert response.status_code == 200
    assert settings.ACCESS_COOKIE_NAME in response.cookies
    assert response.cookies[settings.REFRESH_COOKIE_NAME].value != original_refresh


@pytest.mark.django_db
def test_logout_clears_tokens(csrf_client: APIClient) -> None:
    csrf_client.post("/api/auth/register", registration_payload(), format="json")

    response = csrf_client.post("/api/auth/logout")

    assert response.status_code == 204
    assert response.cookies[settings.ACCESS_COOKIE_NAME]["max-age"] == 0
    assert response.cookies[settings.REFRESH_COOKIE_NAME]["max-age"] == 0
    assert csrf_client.get("/api/auth/me").status_code == 401


@pytest.mark.django_db
def test_authenticated_comment_uses_account_snapshot(csrf_client: APIClient) -> None:
    csrf_client.post("/api/auth/register", registration_payload(), format="json")
    challenge = issue_challenge(answer="ABC123")

    response = csrf_client.post(
        "/api/comments",
        {
            "username": "Spoofed",
            "email": "spoofed@example.com",
            "text": "Authenticated comment",
            "captcha_id": str(challenge.id),
            "captcha_answer": "ABC123",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["author_name"] == "Alice"
    assert response.json()["author_email"] == "alice@example.com"


@pytest.mark.django_db
def test_invalid_access_cookie_is_rejected() -> None:
    client = APIClient()
    client.cookies[settings.ACCESS_COOKIE_NAME] = "not-a-jwt"

    response = client.get("/api/auth/me")

    assert response.status_code == 401
