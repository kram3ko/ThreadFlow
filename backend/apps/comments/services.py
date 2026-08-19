import uuid
from typing import Any

from django.db import transaction

from apps.comments.html import sanitize_comment_html
from apps.comments.models import Comment


@transaction.atomic
def create_comment(
    *,
    user: Any,
    author_name: str,
    author_email: str,
    homepage: str,
    text: str,
    parent: Comment | None = None,
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
    return comment
