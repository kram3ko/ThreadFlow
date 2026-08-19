import logging
import uuid
from typing import Any

from asgiref.sync import async_to_sync
from channels.exceptions import ChannelFull
from channels.layers import get_channel_layer
from redis.exceptions import RedisError

from apps.comments.models import Comment
from apps.comments.realtime.contracts import CommentEvent, CommentKind, SocketMessageType

logger = logging.getLogger(__name__)

PUBLIC_COMMENT_GROUP = "comments.public"


def comment_payload(comment: Comment) -> dict[str, Any]:
    return {
        "id": str(comment.id),
        "author_name": comment.author_name,
        "author_email": comment.author_email,
        "homepage": comment.homepage,
        "html_text": comment.html_text,
        "text": comment.search_text,
        "parent_id": str(comment.parent_id) if comment.parent_id else None,
        "root_id": str(comment.root_id or comment.id),
        "depth": comment.depth,
        "created_at": comment.created_at.isoformat(),
        "updated_at": comment.updated_at.isoformat(),
        "has_more_replies": False,
        "replies": [],
    }


def publish_comment_created(comment: Comment) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    envelope = {
        "type": SocketMessageType.EVENT,
        "event": CommentEvent.CREATED,
        "event_id": str(uuid.uuid4()),
        "data": {
            "kind": CommentKind.REPLY if comment.parent_id else CommentKind.ROOT,
            "comment": comment_payload(comment),
        },
    }
    try:
        async_to_sync(channel_layer.group_send)(
            PUBLIC_COMMENT_GROUP,
            {"type": CommentEvent.CREATED, "envelope": envelope},
        )
    except ChannelFull, RedisError, OSError:
        logger.warning("Live comment delivery failed", exc_info=True)
