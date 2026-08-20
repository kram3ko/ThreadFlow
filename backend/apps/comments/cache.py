from django.core.cache import cache
from django.http import HttpRequest

CACHE_VERSION_KEY = "comments:cache-version"


def cache_version() -> int:
    value = cache.get_or_set(CACHE_VERSION_KEY, 1, timeout=None)
    return value if isinstance(value, int) else 1


def response_cache_key(request: HttpRequest, *, scope: str) -> str:
    return f"comments:{cache_version()}:{scope}:{request.get_host()}:{request.get_full_path()}"


def invalidate_comment_cache() -> None:
    if cache.add(CACHE_VERSION_KEY, 2, timeout=None):
        return
    cache.incr(CACHE_VERSION_KEY)
