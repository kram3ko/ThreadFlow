from config.api.views import health
from django.urls import include, path

urlpatterns = [
    path("health", health, name="health"),
    path("auth/", include("apps.accounts.api.urls")),
    path("captcha", include("apps.captcha.api.urls")),
    path("", include("apps.attachments.api.urls")),
    path("search", include("apps.search.api.urls")),
    path("", include("apps.comments.api.urls")),
]
