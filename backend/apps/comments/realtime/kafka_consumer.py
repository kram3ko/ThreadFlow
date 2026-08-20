from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db.models import Prefetch

from apps.attachments.models import Attachment, AttachmentPurpose
from apps.comments.models import Comment
from apps.comments.realtime.contracts import CommentEvent, SocketMessageType
from apps.comments.realtime.publisher import PUBLIC_COMMENT_GROUP, comment_payload
from apps.events.contracts import ConsumerName, EventEnvelope, EventType
from apps.events.kafka import consume_forever
from apps.events.processing import process_with_retry


def _broadcast(envelope: EventEnvelope) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    if envelope.event_type == EventType.COMMENT_CREATED:
        comment = (
            Comment.objects.select_related("user")
            .prefetch_related(
                "attachments",
                Prefetch(
                    "user__uploads",
                    queryset=Attachment.objects.filter(purpose=AttachmentPurpose.AVATAR).order_by(
                        "-created_at"
                    ),
                    to_attr="avatars",
                ),
            )
            .get(id=envelope.aggregate_id)
        )
        event = CommentEvent.CREATED
        data = {"kind": envelope.payload["kind"], "comment": comment_payload(comment)}
    elif envelope.event_type == EventType.SEARCH_INDEXED:
        event = CommentEvent.SEARCH_INDEXED
        data = envelope.payload
    else:
        return
    async_to_sync(channel_layer.group_send)(
        PUBLIC_COMMENT_GROUP,
        {
            "type": event.replace(".", "_"),
            "envelope": {
                "type": SocketMessageType.EVENT,
                "event": event,
                "event_id": envelope.event_id,
                "data": data,
            },
        },
    )


def run_websocket_consumer() -> None:
    name = ConsumerName.WEBSOCKET
    consume_forever(
        name=name,
        topics=[
            settings.KAFKA_TOPICS["comments_created"],
            settings.KAFKA_TOPICS["search_index"],
            settings.KAFKA_TOPICS["retry"],
        ],
        handler=lambda envelope: process_with_retry(
            envelope=envelope, consumer_name=name, handler=_broadcast
        ),
    )
