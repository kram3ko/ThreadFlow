import time
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from apps.observability.metrics import HTTP_REQUEST_DURATION, HTTP_REQUESTS


class MetricsMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = time.perf_counter()
        response = self.get_response(request)
        route = request.resolver_match.route if request.resolver_match else "unmatched"
        HTTP_REQUEST_DURATION.labels(request.method, route).observe(time.perf_counter() - start)
        HTTP_REQUESTS.labels(request.method, route, str(response.status_code)).inc()
        return response
