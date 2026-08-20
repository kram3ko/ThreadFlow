import hashlib
import io
import secrets
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import puremagic
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from PIL import Image, UnidentifiedImageError
from rest_framework import serializers

from apps.attachments.models import Attachment, AttachmentKind, AttachmentPurpose

ALLOWED_IMAGE_MIME = {"image/jpeg": "jpg", "image/png": "png", "image/gif": "gif"}
TEXT_MIME = {"text/plain"}


@dataclass(frozen=True, slots=True)
class StoredAttachment:
    attachment: Attachment
    claim_token: str


def _detected_mime(content: bytes) -> str:
    try:
        return str(puremagic.from_string(content, mime=True))
    except puremagic.PureError:
        return ""


def _prepare_image(content: bytes, mime: str) -> tuple[bytes, int, int]:
    try:
        with Image.open(io.BytesIO(content)) as image:
            image.verify()
        with Image.open(io.BytesIO(content)) as image:
            image.thumbnail((settings.IMAGE_MAX_WIDTH, settings.IMAGE_MAX_HEIGHT))
            output = io.BytesIO()
            formats = {"image/jpeg": "JPEG", "image/png": "PNG", "image/gif": "GIF"}
            image.save(output, format=formats[mime])
            return output.getvalue(), image.width, image.height
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise serializers.ValidationError({"file": "Invalid image content."}) from exc


def store_upload(*, upload: UploadedFile, user: Any, purpose: str) -> StoredAttachment:
    if upload.size > settings.ATTACHMENT_MAX_BYTES:
        raise serializers.ValidationError({"file": "File exceeds the 10 MB limit."})
    content = upload.read()
    mime = _detected_mime(content)
    width = height = None
    if mime in ALLOWED_IMAGE_MIME:
        kind = AttachmentKind.IMAGE
        content, width, height = _prepare_image(content, mime)
        extension = ALLOWED_IMAGE_MIME[mime]
    elif mime in TEXT_MIME or (
        mime == "" and Path(upload.name or "upload").suffix.lower() == ".txt"
    ):
        if len(content) > settings.TXT_MAX_BYTES:
            raise serializers.ValidationError({"file": "Text file exceeds the 100 KB limit."})
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise serializers.ValidationError({"file": "Text files must use UTF-8."}) from exc
        kind = AttachmentKind.TEXT
        mime = "text/plain"
        extension = "txt"
    else:
        raise serializers.ValidationError({"file": "Only JPG, PNG, GIF and TXT are accepted."})

    if purpose == AttachmentPurpose.AVATAR and kind != AttachmentKind.IMAGE:
        raise serializers.ValidationError({"purpose": "An avatar must be an image."})
    if purpose == AttachmentPurpose.AVATAR and not user.is_authenticated:
        raise serializers.ValidationError({"purpose": "Authentication is required for avatars."})

    token = secrets.token_urlsafe(32)
    attachment_id = uuid.uuid4()
    filename = f"{attachment_id.hex}.{extension}"
    attachment = Attachment(
        id=attachment_id,
        owner=user if user.is_authenticated else None,
        purpose=purpose,
        kind=kind,
        original_name=Path(upload.name or "upload").name[:255],
        content_type=mime,
        size=len(content),
        width=width,
        height=height,
        claim_token_hash=hashlib.sha256(token.encode()).hexdigest(),
    )
    attachment.file.save(filename, ContentFile(content), save=False)
    try:
        attachment.save()
    except Exception:
        attachment.file.delete(save=False)
        raise
    return StoredAttachment(attachment=attachment, claim_token=token)


def claim_attachments(*, claims: list[dict[str, Any]], comment: Any, user: Any) -> None:
    for claim in claims:
        attachment = Attachment.objects.select_for_update().get(
            id=claim["id"], purpose=AttachmentPurpose.COMMENT, comment__isnull=True
        )
        token_matches = secrets.compare_digest(
            attachment.claim_token_hash,
            hashlib.sha256(claim["token"].encode()).hexdigest(),
        )
        owner_matches = user.is_authenticated and attachment.owner_id == user.id
        if not token_matches and not owner_matches:
            raise serializers.ValidationError({"attachments": "Invalid attachment claim."})
        attachment.comment = comment
        attachment.claim_token_hash = ""
        attachment.save(update_fields=["comment", "claim_token_hash"])
