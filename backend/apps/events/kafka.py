import logging
from collections.abc import Callable

from confluent_kafka import Consumer, KafkaError, KafkaException, Message, Producer
from django.conf import settings

from apps.events.contracts import EventEnvelope

logger = logging.getLogger(__name__)
FLUSH_TIMEOUT_SECONDS = 10
POLL_TIMEOUT_SECONDS = 1


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


def publish_event(instance: Producer, *, topic: str, envelope: EventEnvelope, key: str) -> None:
    delivery_error: list[str] = []

    def delivered(error, message) -> None:
        if error is not None:
            delivery_error.append(str(error))

    instance.produce(topic, key=key.encode(), value=envelope.encode(), on_delivery=delivered)
    remaining = instance.flush(FLUSH_TIMEOUT_SECONDS)
    if remaining or delivery_error:
        raise KafkaException(delivery_error[0] if delivery_error else "Kafka delivery timed out")


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
            value = message.value()
            if value is None:
                continue
            handler(EventEnvelope.decode(value))
            instance.commit(message=message, asynchronous=False)
    finally:
        instance.close()
