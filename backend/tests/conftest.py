import pytest
from django.core.cache import caches


@pytest.fixture(autouse=True)
def isolated_cache(settings) -> None:
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "threadflow-tests",
        }
    }
    caches["default"].clear()
