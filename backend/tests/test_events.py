import uuid
from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest
from apps.events.contracts import EventEnvelope
from apps.events.models import OutboxEvent, ProcessedEvent
from apps.events.processing import process_once
from apps.events.publisher import publish_pending_batch


@pytest.mark.django_db
def test_outbox_publisher_marks_acknowledged_events():
    event = OutboxEvent.objects.create(
        event_type="comments.created",
        aggregate_id=uuid.uuid4(),
        payload={"root_id": str(uuid.uuid4())},
    )
    with (
        patch("apps.events.publisher.producer", return_value=Mock()),
        patch("apps.events.publisher.publish_event") as publish,
    ):
        assert publish_pending_batch() == 1
    event.refresh_from_db()
    assert event.published_at is not None
    assert event.attempts == 1
    publish.assert_called_once()


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
