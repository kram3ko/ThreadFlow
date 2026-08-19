import uuid

from apps.captcha.services import CaptchaResult, issue_challenge, verify_challenge
from django.test import override_settings
from rest_framework.test import APIClient


def test_captcha_endpoint_returns_png_data_without_caching():
    response = APIClient().get("/api/captcha")

    assert response.status_code == 200
    assert uuid.UUID(response.json()["id"])
    assert response.json()["image_data"].startswith("data:image/png;base64,")
    assert response.json()["expires_in"] == 300
    assert (
        response.headers["Cache-Control"]
        == "max-age=0, no-cache, no-store, must-revalidate, private"
    )


def test_captcha_answer_is_case_insensitive_and_one_time():
    challenge = issue_challenge(answer="A7K9P2")

    assert verify_challenge(challenge.id, "a7k9p2") is CaptchaResult.VALID
    assert verify_challenge(challenge.id, "A7K9P2") is CaptchaResult.EXPIRED


@override_settings(CAPTCHA_MAX_ATTEMPTS=2)
def test_captcha_expires_after_maximum_attempts():
    challenge = issue_challenge(answer="A7K9P2")

    assert verify_challenge(challenge.id, "WRONG1") is CaptchaResult.INVALID
    assert verify_challenge(challenge.id, "WRONG2") is CaptchaResult.INVALID
    assert verify_challenge(challenge.id, "A7K9P2") is CaptchaResult.EXPIRED
