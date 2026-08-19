from django.utils.csp import CSP
from django.views.decorators.csp import csp_override
from drf_spectacular.views import SpectacularRedocView, SpectacularSwaggerSplitView

API_DOCS_CSP = {
    "default-src": [CSP.SELF],
    "base-uri": [CSP.SELF],
    "connect-src": [CSP.SELF],
    "font-src": [CSP.SELF],
    "frame-ancestors": [CSP.NONE],
    "img-src": [CSP.SELF, "data:"],
    "object-src": [CSP.NONE],
    "script-src": [CSP.SELF],
    "style-src": [CSP.SELF, CSP.UNSAFE_INLINE],
}

swagger_view = csp_override(API_DOCS_CSP)(
    SpectacularSwaggerSplitView.as_view(url_name="api-schema")
)
redoc_view = csp_override(API_DOCS_CSP)(SpectacularRedocView.as_view(url_name="api-schema"))

__all__ = ["redoc_view", "swagger_view"]
