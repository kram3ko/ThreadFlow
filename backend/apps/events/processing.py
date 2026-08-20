import logging
import time
import uuid
from collections.abc import Callable

from django.conf import settings
from django.db import IntegrityError

from apps.events.contracts import EventEnvelope
from apps.events.kafka import producer, publish_event
from apps.events.models import ProcessedEvent

logger = logging.getLogger(__name__)


def process_once(
    *, envelope: EventEnvelope, consumer_name: str, handler: Callable[[EventEnvelope], None]
) -> bool:
    event_id = uuid.UUID(envelope.event_id)
    if ProcessedEvent.objects.filter(event_id=event_id, consumer_name=consumer_name).exists():
        return False
    handler(envelope)
    try:
        ProcessedEvent.objects.create(event_id=event_id, consumer_name=consumer_name)
    except IntegrityError:
        return False
    return True


def process_with_retry(
    *, envelope: EventEnvelope, consumer_name: str, handler: Callable[[EventEnvelope], None]
) -> None:
    if envelope.target_consumer and envelope.target_consumer != consumer_name:
        return
    try:
        process_once(envelope=envelope, consumer_name=consumer_name, handler=handler)
    except Exception as exc:
        attempt = envelope.attempt + 1
        failed = EventEnvelope(
            event_id=envelope.event_id,
            event_type=envelope.event_type,
            aggregate_id=envelope.aggregate_id,
            occurred_at=envelope.occurred_at,
            payload={**envelope.payload, "error": str(exc)[:1000]},
            attempt=attempt,
            target_consumer=consumer_name,
        )
        topic = (
            settings.KAFKA_TOPICS["dlq"]
            if attempt >= settings.KAFKA_RETRY_MAX_ATTEMPTS
            else settings.KAFKA_TOPICS["retry"]
        )
        if topic == settings.KAFKA_TOPICS["retry"]:
            time.sleep(settings.KAFKA_RETRY_BACKOFF_SECONDS * min(attempt, 6))
        publish_event(producer(), topic=topic, envelope=failed, key=envelope.aggregate_id)
        logger.warning("Event %s sent to %s", envelope.event_id, topic)
