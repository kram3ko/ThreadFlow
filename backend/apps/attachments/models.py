import uuid
from enum import StrEnum
from typing import TYPE_CHECKING, ClassVar

from django.conf import settings
from django.db import models


class AttachmentKind(StrEnum):
    IMAGE = "image"
    TEXT = "text"


class AttachmentPurpose(StrEnum):
    COMMENT = "comment"
    AVATAR = "avatar"


class Attachment(models.Model):
    if TYPE_CHECKING:
        comment_id: uuid.UUID | None
        owner_id: uuid.UUID | None

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comment = models.ForeignKey(
        "comments.Comment",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploads",
    )
    purpose = models.CharField(
        max_length=16,
        choices=[(value.value, value.name.title()) for value in AttachmentPurpose],
        default=AttachmentPurpose.COMMENT,
    )
    kind = models.CharField(
        max_length=16,
        choices=[(value.value, value.name.title()) for value in AttachmentKind],
    )
    original_name = models.CharField(max_length=255)
    file = models.FileField(upload_to="uploads/%Y/%m/%d")
    content_type = models.CharField(max_length=64)
    size = models.PositiveIntegerField()
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    claim_token_hash = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes: ClassVar[list[models.Index]] = [models.Index(fields=["comment", "created_at"])]

    def __str__(self) -> str:
        return self.original_name
