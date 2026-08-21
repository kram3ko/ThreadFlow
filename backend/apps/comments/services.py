import uuid
from typing import Any

from django.db import transaction

from apps.comments.cache import invalidate_comment_cache
from apps.comments.html import sanitize_comment_html
from apps.comments.models import Comment
from apps.comments.realtime.publisher import comment_payload
from apps.events.contracts import EventType
from apps.events.models import OutboxEvent
from apps.observability.metrics import COMMENTS_CREATED


@transaction.atomic
def create_comment(
    *,
    user: Any,
    author_name: str,
    author_email: str,
    homepage: str,
    text: str,
    parent: Comment | None = None,
    attachments: list[dict[str, Any]] | None = None,
) -> Comment:
    comment_id = uuid.uuid4()
    html_text, search_text = sanitize_comment_html(text)
    if user and user.is_authenticated:
        author_name = user.username
        author_email = user.email

    comment = Comment(
        id=comment_id,
        user=user if user and user.is_authenticated else None,
        author_name=author_name,
        author_email=author_email,
        homepage=homepage,
        html_text=html_text,
        search_text=search_text,
        parent=parent,
        root=parent.root if parent else None,
        depth=parent.depth + 1 if parent else 0,
    )
    if parent is None:
        comment.root_id = comment_id
    comment.save()
    if attachments:
        from apps.attachments.services import claim_attachments

        claim_attachments(claims=attachments, comment=comment, user=user)
    kind = "reply" if comment.parent_id else "root"
    OutboxEvent.record(
        event_type=EventType.COMMENT_CREATED,
        aggregate_id=comment.id,
        payload={
            "root_id": str(comment.root_id or comment.id),
            "kind": kind,
            "comment": comment_payload(comment),
        },
    )
    transaction.on_commit(invalidate_comment_cache)
    transaction.on_commit(lambda: COMMENTS_CREATED.labels(kind).inc())
    return comment
