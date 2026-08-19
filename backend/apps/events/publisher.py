import logging

from confluent_kafka import KafkaException
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.events.contracts import EventEnvelope
from apps.events.kafka import producer, publish_event
from apps.events.models import OutboxEvent

logger = logging.getLogger(__name__)
LOCK_KEY = "outbox:publisher:lock"


def publish_pending_batch() -> int:
    if not cache.add(LOCK_KEY, "1", timeout=30):
        return 0
    sent = 0
    instance = producer()
    try:
        pending = list(
            OutboxEvent.objects.filter(published_at__isnull=True).order_by("created_at")[
                : settings.OUTBOX_BATCH_SIZE
            ]
        )
        for event in pending:
            envelope = EventEnvelope.create(
                event_id=event.id,
                event_type=event.event_type,
                aggregate_id=event.aggregate_id,
                occurred_at=event.created_at,
                payload=event.payload,
            )
            key = str(event.payload.get("root_id", event.aggregate_id))
            try:
                publish_event(instance, topic=event.event_type, envelope=envelope, key=key)
            except KafkaException as exc:
                OutboxEvent.objects.filter(id=event.id).update(
                    attempts=F("attempts") + 1,
                    last_error=str(exc)[:2000],
                )
                logger.warning("Outbox delivery failed for %s", event.id)
                continue
            with transaction.atomic():
                OutboxEvent.objects.filter(id=event.id, published_at__isnull=True).update(
                    published_at=timezone.now(),
                    attempts=F("attempts") + 1,
                    last_error="",
                )
            sent += 1
    finally:
        cache.delete(LOCK_KEY)
    return sent
