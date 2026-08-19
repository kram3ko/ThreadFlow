import pytest
from django.core.cache import caches
from rest_framework.throttling import ScopedRateThrottle


@pytest.fixture(autouse=True)
def isolated_cache(settings) -> None:
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "threadflow-tests",
        }
    }
    ScopedRateThrottle.cache = caches["default"]
    ScopedRateThrottle.cache.clear()
