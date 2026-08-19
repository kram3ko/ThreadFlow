from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView

from config.api_docs import redoc_view, swagger_view

urlpatterns = [
    path("api/schema", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/docs", swagger_view, name="api-docs"),
    path("api/redoc", redoc_view, name="api-redoc"),
    path("api/", include("apps.api_urls")),
]
