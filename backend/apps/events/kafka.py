import logging
import uuid
from base64 import b64encode
from collections.abc import Callable
from dataclasses import dataclass

import orjson
from confluent_kafka import Consumer, KafkaError, KafkaException, Message, Producer
from django.conf import settings
from django.utils import timezone

from apps.events.contracts import EventEnvelope

logger = logging.getLogger(__name__)
FLUSH_TIMEOUT_SECONDS = 10
POLL_TIMEOUT_SECONDS = 1
MALFORMED_EVENT_TYPE = "events.malformed"
MALFORMED_PAYLOAD_MAX_BYTES = 4096


@dataclass(frozen=True, slots=True)
class KafkaRecord:
    topic: str
    envelope: EventEnvelope
    key: str


def producer() -> Producer:
    return Producer(
        {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "client.id": settings.KAFKA_CLIENT_ID,
            "enable.idempotence": True,
            "acks": "all",
        }
    )


def consumer(*, name: str, topics: list[str]) -> Consumer:
    instance = Consumer(
        {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": f"{settings.KAFKA_CONSUMER_GROUP_PREFIX}.{name}",
            "client.id": f"{settings.KAFKA_CLIENT_ID}.{name}",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    instance.subscribe(topics)
    return instance


def publish_events(instance: Producer, records: list[KafkaRecord]) -> dict[str, str | None]:
    results: dict[str, str | None] = {
        record.envelope.event_id: "Kafka delivery timed out" for record in records
    }

    for record in records:
        event_id = record.envelope.event_id

        def delivered(
            error: KafkaError | None,
            _message: Message,
            event_id: str = event_id,
        ) -> None:
            results[event_id] = str(error) if error is not None else None

        try:
            instance.produce(
                record.topic,
                key=record.key.encode(),
                value=record.envelope.encode(),
                on_delivery=delivered,
            )
        except (BufferError, KafkaException) as exc:
            results[event_id] = str(exc)

    instance.flush(FLUSH_TIMEOUT_SECONDS)
    return results


def publish_event(instance: Producer, *, topic: str, envelope: EventEnvelope, key: str) -> None:
    result = publish_events(
        instance,
        [KafkaRecord(topic=topic, envelope=envelope, key=key)],
    )[envelope.event_id]
    if result is not None:
        raise KafkaException(result)


def _malformed_envelope(message: Message, value: bytes, error: Exception) -> EventEnvelope:
    event_id = str(uuid.uuid4())
    key = message.key()
    return EventEnvelope(
        event_id=event_id,
        event_type=MALFORMED_EVENT_TYPE,
        aggregate_id=event_id,
        occurred_at=timezone.now().isoformat(),
        payload={
            "error": str(error),
            "raw_base64": b64encode(value[:MALFORMED_PAYLOAD_MAX_BYTES]).decode(),
            "source_topic": message.topic(),
            "source_partition": message.partition(),
            "source_offset": message.offset(),
            "source_key": key.decode(errors="replace") if key else None,
            "truncated": len(value) > MALFORMED_PAYLOAD_MAX_BYTES,
        },
    )


def consume_message(
    instance: Consumer,
    message: Message,
    handler: Callable[[EventEnvelope], None],
) -> None:
    value = message.value()
    if value is None:
        instance.commit(message=message, asynchronous=False)
        return
    try:
        envelope = EventEnvelope.decode(value)
    except (orjson.JSONDecodeError, TypeError, ValueError) as exc:
        malformed = _malformed_envelope(message, value, exc)
        publish_event(
            producer(),
            topic=settings.KAFKA_TOPICS["dlq"],
            envelope=malformed,
            key=malformed.event_id,
        )
        logger.warning(
            "Malformed event from %s[%s] offset %s sent to DLQ",
            message.topic(),
            message.partition(),
            message.offset(),
        )
        instance.commit(message=message, asynchronous=False)
        return
    handler(envelope)
    instance.commit(message=message, asynchronous=False)


def consume_forever(
    *, name: str, topics: list[str], handler: Callable[[EventEnvelope], None]
) -> None:
    instance = consumer(name=name, topics=topics)
    try:
        while True:
            message: Message | None = instance.poll(POLL_TIMEOUT_SECONDS)
            if message is None:
                continue
            error = message.error()
            if error:
                if error.code() != KafkaError._PARTITION_EOF:
                    logger.error("Kafka consumer error: %s", error)
                continue
            consume_message(instance, message, handler)
    finally:
        instance.close()
