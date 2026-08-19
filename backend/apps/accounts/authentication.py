from typing import Any

from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from apps.accounts.csrf import enforce_csrf
from apps.accounts.models import User
from apps.accounts.tokens import InvalidTokenError, TokenKind, decode_token


class CookieJWTAuthentication(BaseAuthentication):
    def authenticate(self, request: Request) -> tuple[User, object] | None:
        token = request.COOKIES.get(settings.ACCESS_COOKIE_NAME)
        if not token:
            return None
        try:
            claims = decode_token(token, TokenKind.ACCESS)
        except InvalidTokenError as exc:
            raise AuthenticationFailed(str(exc), code="invalid_token") from exc

        user = User.objects.filter(id=claims.user_id, is_active=True).first()
        if user is None:
            raise AuthenticationFailed("User is inactive or unavailable", code="invalid_token")
        if request.method not in {"GET", "HEAD", "OPTIONS", "TRACE"}:
            enforce_csrf(request)
        return user, claims

    def authenticate_header(self, request: Request) -> str:
        return "Bearer"


class CookieJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "apps.accounts.authentication.CookieJWTAuthentication"
    name = "cookieJwtAuth"

    def get_security_definition(self, auto_schema: Any) -> dict[str, str]:
        return {
            "type": "apiKey",
            "in": "cookie",
            "name": settings.ACCESS_COOKIE_NAME,
            "description": "JWT access token stored in an httpOnly cookie.",
        }


__all__ = ["CookieJWTAuthentication"]
