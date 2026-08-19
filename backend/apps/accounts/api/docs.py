from config.api.docs import ERROR_RESPONSE
from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.accounts.api.serializers import (
    CsrfTokenSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)

document_csrf = extend_schema(
    summary="Initialize CSRF protection",
    description="Sets the readable CSRF cookie used for unsafe SPA requests.",
    responses={200: CsrfTokenSerializer},
    auth=[],
    tags=["authentication"],
)

document_register = extend_schema(
    summary="Register a user",
    request=RegisterSerializer,
    responses={
        201: UserSerializer,
        400: OpenApiResponse(ERROR_RESPONSE, description="Validation failed"),
        403: OpenApiResponse(ERROR_RESPONSE, description="CSRF validation failed"),
    },
    auth=[],
    tags=["authentication"],
)

document_login = extend_schema(
    summary="Sign in",
    request=LoginSerializer,
    responses={
        200: UserSerializer,
        401: OpenApiResponse(ERROR_RESPONSE, description="Invalid credentials"),
        403: OpenApiResponse(ERROR_RESPONSE, description="CSRF validation failed"),
    },
    auth=[],
    tags=["authentication"],
)

document_refresh = extend_schema(
    summary="Rotate authentication tokens",
    request=None,
    responses={
        200: UserSerializer,
        401: OpenApiResponse(ERROR_RESPONSE, description="Refresh token is unavailable or invalid"),
        403: OpenApiResponse(ERROR_RESPONSE, description="CSRF validation failed"),
    },
    auth=[],
    tags=["authentication"],
)

document_logout = extend_schema(
    summary="Sign out",
    request=None,
    responses={
        204: None,
        403: OpenApiResponse(ERROR_RESPONSE, description="CSRF validation failed"),
    },
    auth=[],
    tags=["authentication"],
)

document_me = extend_schema(
    summary="Get the current user",
    responses={
        200: UserSerializer,
        401: OpenApiResponse(ERROR_RESPONSE, description="Authentication required"),
    },
    tags=["authentication"],
)

__all__ = [
    "document_csrf",
    "document_login",
    "document_logout",
    "document_me",
    "document_refresh",
    "document_register",
]
