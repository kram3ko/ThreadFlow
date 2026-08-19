import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

import jwt
from django.conf import settings


class TokenKind(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


@dataclass(frozen=True, slots=True)
class TokenClaims:
    user_id: uuid.UUID
    kind: TokenKind
    token_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class TokenPair:
    access: str
    refresh: str


class InvalidTokenError(ValueError):
    pass


def issue_token_pair(user_id: uuid.UUID) -> TokenPair:
    return TokenPair(
        access=_encode(user_id, TokenKind.ACCESS),
        refresh=_encode(user_id, TokenKind.REFRESH),
    )


def decode_token(token: str, expected_kind: TokenKind) -> TokenClaims:
    secret = _secret_for(expected_kind)
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
            options={"require": ["aud", "exp", "iat", "iss", "jti", "sub", "type"]},
        )
        kind = TokenKind(payload["type"])
        if kind is not expected_kind:
            raise InvalidTokenError("Unexpected token type")
        return TokenClaims(
            user_id=uuid.UUID(payload["sub"]),
            kind=kind,
            token_id=uuid.UUID(payload["jti"]),
        )
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise InvalidTokenError("Invalid or expired token") from exc


def _encode(user_id: uuid.UUID, kind: TokenKind) -> str:
    now = datetime.now(UTC)
    lifetime = (
        timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
        if kind is TokenKind.ACCESS
        else timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    )
    payload = {
        "aud": settings.JWT_AUDIENCE,
        "exp": now + lifetime,
        "iat": now,
        "iss": settings.JWT_ISSUER,
        "jti": str(uuid.uuid4()),
        "sub": str(user_id),
        "type": kind.value,
    }
    return jwt.encode(payload, _secret_for(kind), algorithm=settings.JWT_ALGORITHM)


def _secret_for(kind: TokenKind) -> str:
    return settings.JWT_ACCESS_SECRET if kind is TokenKind.ACCESS else settings.JWT_REFRESH_SECRET


__all__ = [
    "InvalidTokenError",
    "TokenClaims",
    "TokenKind",
    "TokenPair",
    "decode_token",
    "issue_token_pair",
]
