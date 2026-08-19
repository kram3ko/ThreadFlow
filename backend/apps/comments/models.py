import uuid
from typing import TYPE_CHECKING, ClassVar

from django.conf import settings
from django.db import models
from django.db.models import Q


class Comment(models.Model):
    if TYPE_CHECKING:
        parent_id: uuid.UUID | None
        root_id: uuid.UUID | None

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="comments",
    )
    author_name = models.CharField(max_length=150)
    author_email = models.EmailField()
    homepage = models.URLField(blank=True)
    html_text = models.TextField()
    search_text = models.TextField()
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
    )
    root = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="branch_comments",
    )
    depth = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at", "-id"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["parent", "created_at"]),
            models.Index(fields=["root", "created_at"]),
            models.Index(
                fields=["-created_at", "-id"],
                name="comment_root_date_idx",
                condition=Q(parent__isnull=True),
            ),
            models.Index(
                fields=["author_name", "id"],
                name="comment_root_name_idx",
                condition=Q(parent__isnull=True),
            ),
            models.Index(
                fields=["author_email", "id"],
                name="comment_root_email_idx",
                condition=Q(parent__isnull=True),
            ),
        ]
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                condition=Q(parent__isnull=False) | Q(depth=0),
                name="root_comment_depth_zero",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.author_name}: {self.search_text[:40]}"
