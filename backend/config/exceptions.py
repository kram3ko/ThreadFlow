from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    details = response.data
    response.data = {
        "error": {
            "code": getattr(exc, "default_code", "api_error"),
            "details": details,
        }
    }
    return response
