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


def check_comment_rate_limit(identity: str) -> RateLimitResult:
    now = int(time.time())
    retry_after = 60 - now % 60
    window = now // 60
    key = f"comment-rate:{identity}:{window}"
    if cache.add(key, 1, timeout=retry_after + 1):
        return RateLimitResult(allowed=True, retry_after=retry_after)
    count = cache.incr(key)
    return RateLimitResult(
        allowed=count <= settings.COMMENT_RATE_LIMIT_PER_MINUTE,
        retry_after=retry_after,
    )


class CommentRateThrottle(BaseThrottle):
    retry_after = 0

    def allow_request(self, request: Request, view: object) -> bool:
        identity = (
            f"user:{request.user.pk}"
            if request.user.is_authenticated
            else f"guest:{self.get_ident(request)}"
        )
        result = check_comment_rate_limit(identity)
        self.retry_after = result.retry_after
        return result.allowed

    def wait(self) -> int:
        return self.retry_after
