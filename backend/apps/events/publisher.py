import logging
from collections.abc import Iterator
from contextlib import contextmanager
from functools import cache as memoize

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from redis import Redis
from redis.exceptions import RedisError
from redis.lock import Lock

from apps.events.contracts import EventEnvelope, EventType
from apps.events.kafka import KafkaRecord, producer, publish_events
from apps.events.models import OutboxEvent
from apps.observability.metrics import EVENTS_PUBLISHED

logger = logging.getLogger(__name__)
LOCK_KEY = "outbox:publisher:lock"
LOCK_TTL_SECONDS = 30
ERROR_MAX_CHARS = 2000

# Maps each outbox event type to its Kafka topic key so topic names have a
# single source of truth in settings.KAFKA_TOPICS.
OUTBOX_TOPIC_KEYS: dict[str, str] = {
    EventType.COMMENT_CREATED: "comments_created",
}


@memoize
def redis_client() -> Redis:
    if not settings.REDIS_URL:
        raise RedisError("REDIS_URL is required by the outbox publisher")
    return Redis.from_url(settings.REDIS_URL)


@contextmanager
def publisher_lock() -> Iterator[Lock | None]:
    try:
        lock = redis_client().lock(LOCK_KEY, timeout=LOCK_TTL_SECONDS, blocking=False)
        acquired = lock.acquire(blocking=False)
    except RedisError:
        logger.exception("Unable to acquire the outbox publisher lock")
        yield None
        return
    if not acquired:
        yield None
        return
    try:
        yield lock
    finally:
        try:
            lock.release()
        except RedisError:
            logger.warning("Outbox publisher lock expired before release")


def publish_pending_batch() -> int:
    with publisher_lock() as lock:
        if lock is None:
            return 0
        pending = list(
            OutboxEvent.objects.filter(published_at__isnull=True).order_by("created_at")[
                : settings.OUTBOX_BATCH_SIZE
            ]
        )
        if not pending:
            return 0

        records: list[KafkaRecord] = []
        events_by_id: dict[str, OutboxEvent] = {}
        routed_to_dlq: set[str] = set()
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
                envelope.payload["outbox_error"] = "Unsupported event type"
                topic_key = "dlq"
                routed_to_dlq.add(str(event.id))
            key = str(event.payload.get("root_id", event.aggregate_id))
            records.append(
                KafkaRecord(
                    topic=settings.KAFKA_TOPICS[topic_key],
                    envelope=envelope,
                    key=key,
                )
            )
            events_by_id[envelope.event_id] = event

        try:
            lock.extend(LOCK_TTL_SECONDS, replace_ttl=True)
        except RedisError:
            logger.warning("Outbox publisher lock expired before delivery")
            return 0

        results = publish_events(producer(), records)
        sent = 0
        with transaction.atomic():
            for event_id, error in results.items():
                event = events_by_id[event_id]
                if error is not None:
                    OutboxEvent.objects.filter(id=event.id).update(
                        attempts=F("attempts") + 1,
                        last_error=error[:ERROR_MAX_CHARS],
                    )
                    logger.warning("Outbox delivery failed for %s", event.id)
                    continue
                OutboxEvent.objects.filter(id=event.id).update(
                    published_at=timezone.now(),
                    attempts=F("attempts") + 1,
                    last_error=(
                        "Unsupported event type routed to DLQ" if event_id in routed_to_dlq else ""
                    ),
                )
                EVENTS_PUBLISHED.labels(event.event_type).inc()
                sent += 1
        return sent
