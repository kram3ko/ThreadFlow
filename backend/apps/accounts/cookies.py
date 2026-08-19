from django.conf import settings
from rest_framework.response import Response

from apps.accounts.tokens import TokenPair


def set_auth_cookies(
    response: Response,
    tokens: TokenPair,
    *,
    include_refresh: bool = True,
) -> None:
    response.set_cookie(
        settings.ACCESS_COOKIE_NAME,
        tokens.access,
        max_age=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )
    if include_refresh:
        response.set_cookie(
            settings.REFRESH_COOKIE_NAME,
            tokens.refresh,
            max_age=settings.JWT_REFRESH_EXPIRE_DAYS * 86_400,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            path="/api/auth",
        )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        settings.ACCESS_COOKIE_NAME,
        path="/",
        samesite=settings.COOKIE_SAMESITE,
    )
    response.delete_cookie(
        settings.REFRESH_COOKIE_NAME,
        path="/api/auth",
        samesite=settings.COOKIE_SAMESITE,
    )


__all__ = ["clear_auth_cookies", "set_auth_cookies"]
