import logging
import uuid
from typing import Any

from asgiref.sync import async_to_sync
from channels.exceptions import ChannelFull
from channels.layers import get_channel_layer
from redis.exceptions import RedisError

from apps.comments.models import Comment
from apps.comments.realtime.contracts import CommentEvent, CommentKind, SocketMessageType

PUBLIC_COMMENT_GROUP = "comments.public"
logger = logging.getLogger(__name__)


def comment_payload(comment: Comment) -> dict[str, Any]:
    attachments = [
        {
            "id": str(item.id),
            "kind": item.kind,
            "purpose": item.purpose,
            "original_name": item.original_name,
            "content_type": item.content_type,
            "size": item.size,
            "width": item.width,
            "height": item.height,
            "content_url": f"/api/attachments/{item.id}/content",
        }
        for item in comment.attachments.all()
    ]
    prefetched = getattr(comment.user, "avatars", None) if comment.user_id else None
    if prefetched is not None:
        avatar = prefetched[0] if prefetched else None
    else:
        avatar = (
            comment.user.uploads.filter(purpose="avatar").order_by("-created_at").first()
            if comment.user_id
            else None
        )
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
        "score": comment.score,
        "created_at": comment.created_at.isoformat(),
        "updated_at": comment.updated_at.isoformat(),
        "has_more_replies": False,
        "avatar_url": f"/api/attachments/{avatar.id}/content" if avatar else None,
        "attachments": attachments,
        "replies": [],
    }


def publish_comment_created(comment: Comment, *, event_id: str | None = None) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    envelope = {
        "type": SocketMessageType.EVENT,
        "event": CommentEvent.CREATED,
        "event_id": event_id or str(uuid.uuid4()),
        "data": {
            "kind": CommentKind.REPLY if comment.parent_id else CommentKind.ROOT,
            "comment": comment_payload(comment),
        },
    }
    async_to_sync(channel_layer.group_send)(
        PUBLIC_COMMENT_GROUP,
        {"type": CommentEvent.CREATED, "envelope": envelope},
    )


def publish_comment_voted(comment_id: str, score: int) -> bool:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return False
    envelope = {
        "type": SocketMessageType.EVENT,
        "event": CommentEvent.VOTED,
        "event_id": str(uuid.uuid4()),
        "data": {"comment_id": comment_id, "score": score},
    }
    try:
        async_to_sync(channel_layer.group_send)(
            PUBLIC_COMMENT_GROUP,
            {"type": CommentEvent.VOTED, "envelope": envelope},
        )
    except ChannelFull, RedisError, TimeoutError:
        logger.warning("Unable to publish vote update for comment %s", comment_id)
        return False
    return True
