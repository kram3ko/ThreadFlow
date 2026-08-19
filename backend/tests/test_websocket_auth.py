import pytest
from apps.accounts.models import User
from apps.accounts.tokens import issue_token_pair
from apps.accounts.ws import CookieJWTWebSocketMiddleware


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_websocket_access_cookie_resolves_active_user(settings):
    user = await User.objects.acreate(username="SocketUser", email="socket-user@example.com")
    token = issue_token_pair(user.id).access
    captured = {}

    async def app(scope, receive, send):
        captured.update(scope)

    middleware = CookieJWTWebSocketMiddleware(app)
    await middleware(
        {
            "type": "websocket",
            "headers": [(b"cookie", f"other=1; {settings.ACCESS_COOKIE_NAME}={token}".encode())],
        },
        None,
        None,
    )

    assert captured["user"].id == user.id
    assert captured["auth_error"] is False


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_websocket_invalid_cookie_is_marked_as_auth_error(settings):
    captured = {}

    async def app(scope, receive, send):
        captured.update(scope)

    middleware = CookieJWTWebSocketMiddleware(app)
    await middleware(
        {
            "type": "websocket",
            "headers": [(b"cookie", f"{settings.ACCESS_COOKIE_NAME}=invalid".encode())],
        },
        None,
        None,
    )

    assert captured["user"].is_anonymous
    assert captured["auth_error"] is True
