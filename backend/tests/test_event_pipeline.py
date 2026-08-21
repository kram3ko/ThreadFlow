import uuid
from dataclasses import replace
from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest
from apps.comments.models import Comment
from apps.comments.realtime.contracts import CommentEvent
from apps.comments.realtime.kafka_consumer import _broadcast, run_websocket_consumer
from apps.events.contracts import ConsumerName, EventEnvelope, EventType
from apps.events.kafka import KafkaRecord, consume_message, publish_event, publish_events
from apps.events.processing import process_with_retry
from apps.search.consumers import _index
from apps.search.documents import ensure_index, index_comment
from confluent_kafka import KafkaException


def _envelope(*, event_type: str = EventType.COMMENT_CREATED, attempt: int = 0) -> EventEnvelope:
    event_id = str(uuid.uuid4())
    return EventEnvelope(
        event_id=event_id,
        event_type=event_type,
        aggregate_id=str(uuid.uuid4()),
        occurred_at=datetime.now(UTC).isoformat(),
        payload={"root_id": str(uuid.uuid4()), "kind": "root"},
        attempt=attempt,
    )


def test_kafka_batch_reports_acknowledged_and_rejected_records():
    acknowledged = _envelope()
    rejected = _envelope()
    instance = Mock()

    def produce(_topic, **kwargs):
        if kwargs["key"] == b"rejected":
            raise BufferError("queue full")
        kwargs["on_delivery"](None, Mock())

    instance.produce.side_effect = produce
    results = publish_events(
        instance,
        [
            KafkaRecord("comments.created", acknowledged, "acknowledged"),
            KafkaRecord("comments.created", rejected, "rejected"),
        ],
    )

    assert results[acknowledged.event_id] is None
    assert results[rejected.event_id] == "queue full"
    instance.flush.assert_called_once()


def test_single_kafka_publish_raises_when_delivery_fails():
    envelope = _envelope()
    instance = Mock()
    instance.produce.side_effect = BufferError("queue full")

    with pytest.raises(KafkaException, match="queue full"):
        publish_event(instance, topic="comments.created", envelope=envelope, key="root")


def test_kafka_message_dispatches_valid_envelope_and_commits():
    envelope = _envelope()
    instance = Mock()
    message = Mock()
    message.value.return_value = envelope.encode()
    handler = Mock()

    consume_message(instance, message, handler)

    handler.assert_called_once_with(envelope)
    instance.commit.assert_called_once_with(message=message, asynchronous=False)


def test_kafka_tombstone_is_committed_without_dispatch():
    instance = Mock()
    message = Mock()
    message.value.return_value = None
    handler = Mock()

    consume_message(instance, message, handler)

    handler.assert_not_called()
    instance.commit.assert_called_once_with(message=message, asynchronous=False)


@pytest.mark.django_db
def test_failed_consumer_event_is_sent_to_retry(settings):
    settings.KAFKA_RETRY_BACKOFF_SECONDS = 0
    envelope = _envelope()

    with (
        patch("apps.events.processing.time.sleep") as sleep,
        patch("apps.events.processing.producer", return_value=Mock()),
        patch("apps.events.processing.publish_event") as publish,
    ):
        process_with_retry(
            envelope=envelope,
            consumer_name=ConsumerName.SEARCH,
            handler=Mock(side_effect=RuntimeError("index unavailable")),
        )

    failed = publish.call_args.kwargs["envelope"]
    assert publish.call_args.kwargs["topic"] == settings.KAFKA_TOPICS["retry"]
    assert failed.attempt == 1
    assert failed.target_consumer == ConsumerName.SEARCH
    assert failed.payload["error"] == "index unavailable"
    sleep.assert_called_once_with(0)


@pytest.mark.django_db
def test_exhausted_consumer_event_is_sent_to_dlq_without_sleep(settings):
    envelope = _envelope(attempt=settings.KAFKA_RETRY_MAX_ATTEMPTS - 1)

    with (
        patch("apps.events.processing.time.sleep") as sleep,
        patch("apps.events.processing.producer", return_value=Mock()),
        patch("apps.events.processing.publish_event") as publish,
    ):
        process_with_retry(
            envelope=envelope,
            consumer_name=ConsumerName.WEBSOCKET,
            handler=Mock(side_effect=RuntimeError("channel unavailable")),
        )

    assert publish.call_args.kwargs["topic"] == settings.KAFKA_TOPICS["dlq"]
    sleep.assert_not_called()


def test_retry_for_another_consumer_is_ignored():
    envelope = replace(_envelope(), target_consumer=ConsumerName.WEBSOCKET)
    handler = Mock()

    process_with_retry(
        envelope=envelope,
        consumer_name=ConsumerName.SEARCH,
        handler=handler,
    )

    handler.assert_not_called()


def test_search_consumer_indexes_comment_and_emits_completion(settings):
    envelope = _envelope()
    with (
        patch("apps.search.consumers.index_comment") as index,
        patch("apps.search.consumers.producer", return_value=Mock()),
        patch("apps.search.consumers.publish_event") as publish,
    ):
        _index(envelope)

    index.assert_called_once_with(envelope.aggregate_id)
    indexed = publish.call_args.kwargs["envelope"]
    assert indexed.event_type == EventType.SEARCH_INDEXED
    assert publish.call_args.kwargs["topic"] == settings.KAFKA_TOPICS["search_index"]


def test_search_consumer_ignores_unrelated_events():
    with patch("apps.search.consumers.index_comment") as index:
        _index(_envelope(event_type=EventType.SEARCH_INDEXED))
    index.assert_not_called()


@pytest.mark.django_db
def test_search_document_creates_index_and_indexes_comment(settings):
    comment = Comment.objects.create(
        author_name="Indexer",
        author_email="indexer@example.com",
        html_text="Indexed",
        search_text="Indexed",
        depth=0,
    )
    comment.root_id = comment.id
    comment.save(update_fields=["root"])
    elasticsearch = Mock()
    elasticsearch.indices.exists.return_value = False

    index_comment(str(comment.id), elasticsearch)

    elasticsearch.indices.create.assert_called_once()
    assert elasticsearch.index.call_args.kwargs["id"] == str(comment.id)
    assert elasticsearch.index.call_args.kwargs["document"]["text"] == "Indexed"
    assert elasticsearch.index.call_args.kwargs["index"] == settings.ELASTICSEARCH_INDEX


def test_existing_search_index_is_not_recreated():
    elasticsearch = Mock()
    elasticsearch.indices.exists.return_value = True

    ensure_index(elasticsearch)

    elasticsearch.indices.create.assert_not_called()


def test_search_indexed_event_is_broadcast_to_channels():
    envelope = _envelope(event_type=EventType.SEARCH_INDEXED)
    sender = Mock()
    layer = Mock()
    with (
        patch("apps.comments.realtime.kafka_consumer.get_channel_layer", return_value=layer),
        patch("apps.comments.realtime.kafka_consumer.async_to_sync", return_value=sender),
    ):
        _broadcast(envelope)

    message = sender.call_args.args[1]["envelope"]
    assert message["event"] == CommentEvent.SEARCH_INDEXED
    assert message["event_id"] == envelope.event_id


def test_websocket_consumer_subscribes_to_all_delivery_topics(settings):
    with patch("apps.comments.realtime.kafka_consumer.consume_forever") as consume:
        run_websocket_consumer()

    assert consume.call_args.kwargs["name"] == ConsumerName.WEBSOCKET
    assert consume.call_args.kwargs["topics"] == [
        settings.KAFKA_TOPICS["comments_created"],
        settings.KAFKA_TOPICS["search_index"],
        settings.KAFKA_TOPICS["retry"],
    ]
