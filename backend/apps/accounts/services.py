from django.contrib.auth import authenticate
from rest_framework.exceptions import APIException

from apps.accounts.models import User


class AuthenticationRejected(APIException):
    status_code = 401
    default_detail = "Authentication rejected"
    default_code = "authentication_rejected"


def authenticate_user(*, username: str, password: str) -> User:
    """Authenticate by username or email.

    A username can never contain "@" (it is restricted to [A-Za-z0-9_]), so an
    "@" in the value unambiguously identifies an email address.
    """
    login = username
    if "@" in login:
        match = User.objects.filter(email__iexact=User.objects.normalize_email(login)).first()
        if match is not None:
            login = match.username
    user = authenticate(username=login, password=password)
    if user is None or not isinstance(user, User):
        raise AuthenticationRejected("Invalid username or password", code="invalid_credentials")
    if not user.is_active:
        raise AuthenticationRejected("User account is inactive", code="inactive_user")
    return user


__all__ = ["AuthenticationRejected", "authenticate_user"]
