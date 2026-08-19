from django.urls import path

from apps.captcha.api.views import CaptchaChallengeView

urlpatterns = [path("", CaptchaChallengeView.as_view(), name="captcha-challenge")]
