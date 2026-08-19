from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path("api/schema", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/docs", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
    path("api/redoc", SpectacularRedocView.as_view(url_name="api-schema"), name="api-redoc"),
    path("api/", include("apps.api_urls")),
]
