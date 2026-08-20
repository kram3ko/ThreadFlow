import time
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache
from rest_framework.request import Request
from rest_framework.throttling import BaseThrottle


@dataclass(frozen=True, slots=True)
class RateLimitResult:
    allowed: bool
    retry_after: int


def _check_rate_limit(*, scope: str, identity: str, limit: int) -> RateLimitResult:
    now = int(time.time())
    retry_after = 60 - now % 60
    window = now // 60
    key = f"{scope}-rate:{identity}:{window}"
    if cache.add(key, 1, timeout=retry_after + 1):
        return RateLimitResult(allowed=True, retry_after=retry_after)
    count = cache.incr(key)
    return RateLimitResult(
        allowed=count <= limit,
        retry_after=retry_after,
    )


def check_comment_rate_limit(identity: str) -> RateLimitResult:
    return _check_rate_limit(
        scope="comment",
        identity=identity,
        limit=settings.COMMENT_RATE_LIMIT_PER_MINUTE,
    )


def check_vote_rate_limit(identity: str) -> RateLimitResult:
    return _check_rate_limit(
        scope="vote",
        identity=identity,
        limit=settings.VOTE_RATE_LIMIT_PER_MINUTE,
    )


class IdentityRateThrottle(BaseThrottle):
    retry_after = 0

    def check(self, identity: str) -> RateLimitResult:
        raise NotImplementedError

    def allow_request(self, request: Request, view: object) -> bool:
        identity = (
            f"user:{request.user.pk}"
            if request.user.is_authenticated
            else f"guest:{self.get_ident(request)}"
        )
        result = self.check(identity)
        self.retry_after = result.retry_after
        return result.allowed

    def wait(self) -> int:
        return self.retry_after


class CommentRateThrottle(IdentityRateThrottle):
    def check(self, identity: str) -> RateLimitResult:
        return check_comment_rate_limit(identity)


class VoteRateThrottle(IdentityRateThrottle):
    def check(self, identity: str) -> RateLimitResult:
        return check_vote_rate_limit(identity)
