import uuid
from typing import Any, ClassVar

from django.db import models


class OutboxEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=80)
    aggregate_id = models.UUIDField()
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["created_at", "id"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["published_at", "created_at"], name="outbox_pending_created_idx")
        ]

    def __str__(self) -> str:
        return f"{self.event_type}:{self.aggregate_id}"

    @classmethod
    def record(
        cls, *, event_type: str, aggregate_id: uuid.UUID, payload: dict[str, Any]
    ) -> OutboxEvent:
        return cls.objects.create(
            event_type=event_type,
            aggregate_id=aggregate_id,
            payload=payload,
        )


class ProcessedEvent(models.Model):
    event_id = models.UUIDField()
    consumer_name = models.CharField(max_length=80)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["event_id", "consumer_name"], name="unique_event_per_consumer"
            )
        ]

    def __str__(self) -> str:
        return f"{self.consumer_name}:{self.event_id}"
