from config.api.views import health
from django.urls import include, path

urlpatterns = [
    path("health", health, name="health"),
    path("", include("apps.comments.api.urls")),
]
