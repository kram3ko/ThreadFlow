import io

import pytest
from apps.attachments.models import Attachment
from apps.captcha.services import issue_challenge
from apps.events.models import OutboxEvent
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient


def image_upload(width: int = 640, height: int = 480) -> SimpleUploadedFile:
    output = io.BytesIO()
    Image.new("RGB", (width, height), "#286c5d").save(output, format="PNG")
    return SimpleUploadedFile("photo.png", output.getvalue(), content_type="image/png")


@pytest.mark.django_db
def test_image_is_resized_and_claimed_by_comment(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    client = APIClient()
    upload = client.post(
        "/api/attachments",
        {"file": image_upload(), "purpose": "comment"},
        format="multipart",
    )
    assert upload.status_code == 201
    assert upload.json()["width"] == 320
    assert upload.json()["height"] == 240

    challenge = issue_challenge(answer="ABC123")
    response = client.post(
        "/api/comments",
        {
            "username": "AttachmentUser",
            "email": "attachment@example.com",
            "text": "With an image",
            "captcha_id": str(challenge.id),
            "captcha_answer": "ABC123",
            "attachments": [{"id": upload.json()["id"], "token": upload.json()["claim_token"]}],
        },
        format="json",
    )
    assert response.status_code == 201
    attachment = Attachment.objects.get(id=upload.json()["id"])
    assert str(attachment.comment_id) == response.json()["id"]
    assert response.json()["attachments"][0]["kind"] == "image"
    assert OutboxEvent.objects.filter(event_type="attachments.uploaded").exists()


@pytest.mark.django_db
def test_executable_upload_is_rejected(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    response = APIClient().post(
        "/api/attachments",
        {"file": SimpleUploadedFile("payload.jpg", b"MZ executable")},
        format="multipart",
    )
    assert response.status_code == 400
