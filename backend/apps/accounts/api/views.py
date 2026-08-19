from django.conf import settings
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.api.docs import (
    document_csrf,
    document_login,
    document_logout,
    document_me,
    document_refresh,
    document_register,
)
from apps.accounts.api.serializers import LoginSerializer, RegisterSerializer, UserSerializer
from apps.accounts.cookies import clear_auth_cookies, set_auth_cookies
from apps.accounts.csrf import enforce_csrf
from apps.accounts.models import User
from apps.accounts.services import AuthenticationRejected, authenticate_user
from apps.accounts.tokens import InvalidTokenError, TokenKind, decode_token, issue_token_pair


class PublicAuthView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)


class CsrfView(PublicAuthView):
    @document_csrf
    def get(self, request: Request) -> Response:
        return Response({"csrf_token": get_token(request._request)})


class RegisterView(PublicAuthView):
    @document_register
    def post(self, request: Request) -> Response:
        enforce_csrf(request)
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response = Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        set_auth_cookies(response, issue_token_pair(user.id))
        return response


class LoginView(PublicAuthView):
    @document_login
    def post(self, request: Request) -> Response:
        enforce_csrf(request)
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate_user(**serializer.validated_data)
        response = Response(UserSerializer(user).data)
        set_auth_cookies(response, issue_token_pair(user.id))
        return response


class RefreshView(PublicAuthView):
    @document_refresh
    def post(self, request: Request) -> Response:
        enforce_csrf(request)
        token = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
        if not token:
            raise AuthenticationRejected(
                "Refresh token is required",
                code="missing_refresh_token",
            )
        try:
            claims = decode_token(token, TokenKind.REFRESH)
        except InvalidTokenError as exc:
            raise AuthenticationRejected(str(exc), code="invalid_token") from exc
        user = User.objects.filter(id=claims.user_id, is_active=True).first()
        if user is None:
            raise AuthenticationRejected("User is inactive or unavailable", code="invalid_token")

        response = Response(UserSerializer(user).data)
        set_auth_cookies(
            response,
            issue_token_pair(user.id),
            include_refresh=settings.JWT_REFRESH_ROTATION,
        )
        return response


class LogoutView(PublicAuthView):
    @document_logout
    def post(self, request: Request) -> Response:
        enforce_csrf(request)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_auth_cookies(response)
        return response


class MeView(APIView):
    permission_classes = (IsAuthenticated,)

    @document_me
    def get(self, request: Request) -> Response:
        return Response(UserSerializer(request.user).data)


__all__ = ["CsrfView", "LoginView", "LogoutView", "MeView", "RefreshView", "RegisterView"]
