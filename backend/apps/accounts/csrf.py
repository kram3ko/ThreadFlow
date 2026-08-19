from django.http import HttpRequest, HttpResponse
from rest_framework.authentication import CSRFCheck
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request


def enforce_csrf(request: Request) -> None:
    check = CSRFCheck(_empty_response)
    http_request = request._request
    check.process_request(http_request)
    reason = check.process_view(http_request, _empty_response, (), {})
    if reason:
        raise PermissionDenied(f"CSRF failed: {reason}", code="csrf_failed")


def _empty_response(request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
    return HttpResponse()


__all__ = ["enforce_csrf"]
