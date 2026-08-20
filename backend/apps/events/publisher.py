import logging

from confluent_kafka import KafkaException
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.events.contracts import EventEnvelope, EventType
from apps.events.kafka import producer, publish_event
from apps.events.models import OutboxEvent

logger = logging.getLogger(__name__)
LOCK_KEY = "outbox:publisher:lock"
LOCK_TTL_SECONDS = 30
ERROR_MAX_CHARS = 2000

# Maps each outbox event type to its Kafka topic key so topic names have a
# single source of truth in settings.KAFKA_TOPICS.
OUTBOX_TOPIC_KEYS: dict[str, str] = {
    EventType.COMMENT_CREATED: "comments_created",
}


def publish_pending_batch() -> int:
    if not cache.add(LOCK_KEY, "1", timeout=LOCK_TTL_SECONDS):
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
            topic_key = OUTBOX_TOPIC_KEYS.get(event.event_type)
            if topic_key is None:
                logger.warning("No topic mapping for event type %s", event.event_type)
                continue
            key = str(event.payload.get("root_id", event.aggregate_id))
            try:
                topic = settings.KAFKA_TOPICS[topic_key]
                publish_event(instance, topic=topic, envelope=envelope, key=key)
            except KafkaException as exc:
                OutboxEvent.objects.filter(id=event.id).update(
                    attempts=F("attempts") + 1,
                    last_error=str(exc)[:ERROR_MAX_CHARS],
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
