from django.db import transaction
from django.db.models import F
from rest_framework.request import Request
from rest_framework.throttling import BaseThrottle

from apps.comments.models import Comment, CommentVote


def voter_identity(request: Request) -> str:
    if request.user.is_authenticated:
        return f"user:{request.user.pk}"
    return f"guest:{BaseThrottle().get_ident(request)}"


@transaction.atomic
def apply_vote(*, comment: Comment, identity: str, value: int) -> int:
    """Record a voter's choice and return the comment's new score.

    `value` is 1, -1 or 0; zero clears an existing vote. Only the delta against
    the previous vote is applied, so re-voting never double counts.
    """
    existing = (
        CommentVote.objects.select_for_update().filter(comment=comment, identity=identity).first()
    )
    previous = existing.value if existing else 0

    if value == 0:
        if existing:
            existing.delete()
    elif existing:
        existing.value = value
        existing.save(update_fields=["value", "updated_at"])
    else:
        CommentVote.objects.create(comment=comment, identity=identity, value=value)

    delta = value - previous
    if delta:
        Comment.objects.filter(id=comment.id).update(score=F("score") + delta)
    comment.refresh_from_db(fields=["score"])
    return comment.score
