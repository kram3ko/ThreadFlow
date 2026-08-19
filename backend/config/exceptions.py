from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)
    if response is None:
        return None

    details = response.data
    get_codes: Any = getattr(exc, "get_codes", None)
    codes = get_codes() if callable(get_codes) else None
    code = codes if isinstance(codes, str) else getattr(exc, "default_code", "api_error")
    response.data = {
        "error": {
            "code": code,
            "details": details,
        }
    }
    return response
