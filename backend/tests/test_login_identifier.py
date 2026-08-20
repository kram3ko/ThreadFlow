import pytest
from apps.accounts.models import User
from rest_framework.test import APIClient

CREDENTIALS = "Str0ngPass!234"


@pytest.fixture
def account() -> User:
    return User.objects.create_user(
        username="Kramer", email="kramer@example.com", password=CREDENTIALS
    )


@pytest.mark.django_db
@pytest.mark.parametrize("identifier", ["Kramer", "kramer@example.com", "KRAMER@EXAMPLE.COM"])
def test_login_accepts_username_or_email(account: User, identifier: str):
    response = APIClient().post(
        "/api/auth/login",
        {"username": identifier, "password": CREDENTIALS},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["username"] == "Kramer"


@pytest.mark.django_db
def test_login_rejects_wrong_password(account: User):
    response = APIClient().post(
        "/api/auth/login",
        {"username": "kramer@example.com", "password": "wrong"},
        format="json",
    )
    assert response.status_code == 401
