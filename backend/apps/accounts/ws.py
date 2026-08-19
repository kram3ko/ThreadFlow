from http.cookies import SimpleCookie
from typing import Any

from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from apps.accounts.models import User
from apps.accounts.tokens import InvalidTokenError, TokenKind, decode_token


@database_sync_to_async
def _active_user(token: str) -> User | None:
    try:
        claims = decode_token(token, TokenKind.ACCESS)
    except InvalidTokenError:
        return None
    return User.objects.filter(id=claims.user_id, is_active=True).first()


class CookieJWTWebSocketMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        cookie = SimpleCookie()
        for name, value in scope.get("headers", []):
            if name == b"cookie":
                cookie.load(value.decode("latin1"))
                break

        morsel = cookie.get(settings.ACCESS_COOKIE_NAME)
        if morsel is None:
            scope["user"] = AnonymousUser()
        else:
            user = await _active_user(morsel.value)
            scope["user"] = user or AnonymousUser()
            scope["auth_error"] = user is None
        await self.app(scope, receive, send)
