import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest
from apps.events.contracts import EventEnvelope
from apps.events.kafka import consume_message
from apps.events.models import OutboxEvent, ProcessedEvent
from apps.events.processing import process_once
from apps.events.publisher import publish_pending_batch


@contextmanager
def _publisher_lock():
    yield Mock()


@pytest.mark.django_db
def test_outbox_publisher_marks_acknowledged_events():
    event = OutboxEvent.objects.create(
        event_type="comments.created",
        aggregate_id=uuid.uuid4(),
        payload={"root_id": str(uuid.uuid4())},
    )
    with (
        patch("apps.events.publisher.publisher_lock", _publisher_lock),
        patch("apps.events.publisher.producer", return_value=Mock()),
        patch(
            "apps.events.publisher.publish_events",
            return_value={str(event.id): None},
        ) as publish,
    ):
        assert publish_pending_batch() == 1
    event.refresh_from_db()
    assert event.published_at is not None
    assert event.attempts == 1
    publish.assert_called_once()


@pytest.mark.django_db
def test_outbox_publisher_batches_events_and_routes_unknown_types_to_dlq(settings):
    known = OutboxEvent.objects.create(
        event_type="comments.created",
        aggregate_id=uuid.uuid4(),
        payload={"root_id": str(uuid.uuid4())},
    )
    unknown = OutboxEvent.objects.create(
        event_type="attachments.uploaded",
        aggregate_id=uuid.uuid4(),
        payload={},
    )

    def publish(_producer, records):
        assert len(records) == 2
        assert records[0].topic == settings.KAFKA_TOPICS["comments_created"]
        assert records[1].topic == settings.KAFKA_TOPICS["dlq"]
        return {record.envelope.event_id: None for record in records}

    with (
        patch("apps.events.publisher.publisher_lock", _publisher_lock),
        patch("apps.events.publisher.producer", return_value=Mock()),
        patch("apps.events.publisher.publish_events", side_effect=publish),
    ):
        assert publish_pending_batch() == 2

    known.refresh_from_db()
    unknown.refresh_from_db()
    assert known.published_at is not None
    assert unknown.published_at is not None
    assert unknown.last_error == "Unsupported event type routed to DLQ"


@pytest.mark.django_db
def test_outbox_publisher_does_nothing_without_lock():
    @contextmanager
    def unavailable_lock():
        yield None

    with patch("apps.events.publisher.publisher_lock", unavailable_lock):
        assert publish_pending_batch() == 0


def test_malformed_kafka_message_is_sent_to_dlq(settings):
    instance = Mock()
    message = Mock()
    message.value.return_value = b"not-json"
    message.key.return_value = b"branch-id"
    message.topic.return_value = settings.KAFKA_TOPICS["comments_created"]
    message.partition.return_value = 2
    message.offset.return_value = 17
    handler = Mock()

    with (
        patch("apps.events.kafka.producer", return_value=Mock()),
        patch("apps.events.kafka.publish_event") as publish,
    ):
        consume_message(instance, message, handler)

    handler.assert_not_called()
    publish.assert_called_once()
    envelope = publish.call_args.kwargs["envelope"]
    assert publish.call_args.kwargs["topic"] == settings.KAFKA_TOPICS["dlq"]
    assert envelope.event_type == "events.malformed"
    assert envelope.payload["source_offset"] == 17
    instance.commit.assert_called_once_with(message=message, asynchronous=False)


@pytest.mark.django_db
def test_consumer_processing_is_idempotent():
    envelope = EventEnvelope(
        event_id=str(uuid.uuid4()),
        event_type="comments.created",
        aggregate_id=str(uuid.uuid4()),
        occurred_at=datetime.now(UTC).isoformat(),
        payload={},
    )
    handler = Mock()
    assert process_once(envelope=envelope, consumer_name="search", handler=handler)
    assert not process_once(envelope=envelope, consumer_name="search", handler=handler)
    assert handler.call_count == 1
    assert ProcessedEvent.objects.count() == 1
