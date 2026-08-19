import html
import uuid

from django.db import transaction

from apps.comments.models import Comment


@transaction.atomic
def create_comment(*, user, author_name, author_email, homepage, text, parent=None):
    comment_id = uuid.uuid4()
    if user and user.is_authenticated:
        author_name = user.username
        author_email = user.email

    comment = Comment(
        id=comment_id,
        user=user if user and user.is_authenticated else None,
        author_name=author_name,
        author_email=author_email,
        homepage=homepage,
        html_text=html.escape(text),
        search_text=text,
        parent=parent,
        root=parent.root if parent else None,
        depth=parent.depth + 1 if parent else 0,
    )
    if parent is None:
        comment.root_id = comment_id
    comment.save()
    return comment
