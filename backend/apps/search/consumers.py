import uuid

from django.conf import settings

from apps.events.contracts import ConsumerName, EventEnvelope, EventType
from apps.events.kafka import consume_forever, producer, publish_event
from apps.events.processing import process_with_retry
from apps.search.documents import index_comment


def _index(envelope: EventEnvelope) -> None:
    if envelope.event_type != EventType.COMMENT_CREATED:
        return
    index_comment(envelope.aggregate_id)
    indexed = EventEnvelope(
        event_id=str(uuid.uuid4()),
        event_type=EventType.SEARCH_INDEXED,
        aggregate_id=envelope.aggregate_id,
        occurred_at=envelope.occurred_at,
        payload={"comment_id": envelope.aggregate_id, "root_id": envelope.payload["root_id"]},
    )
    publish_event(
        producer(),
        topic=settings.KAFKA_TOPICS["search_index"],
        envelope=indexed,
        key=envelope.payload["root_id"],
    )


def run_search_consumer() -> None:
    name = ConsumerName.SEARCH
    consume_forever(
        name=name,
        topics=[settings.KAFKA_TOPICS["comments_created"], settings.KAFKA_TOPICS["retry"]],
        handler=lambda envelope: process_with_retry(
            envelope=envelope, consumer_name=name, handler=_index
        ),
    )
