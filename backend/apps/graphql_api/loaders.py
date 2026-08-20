import uuid
from dataclasses import dataclass

from channels.db import database_sync_to_async
from django.db.models import Prefetch
from strawberry import ID
from strawberry.dataloader import DataLoader

from apps.attachments.models import Attachment, AttachmentPurpose
from apps.comments.models import Comment
from apps.graphql_api.types import AttachmentNode, AuthorNode, CommentNode


@dataclass(frozen=True, slots=True)
class BranchKey:
    comment_id: uuid.UUID
    depth: int


def _comment_queryset():
    avatars = Attachment.objects.filter(purpose=AttachmentPurpose.AVATAR).order_by("-created_at")
    return Comment.objects.select_related("user").prefetch_related(
        "attachments",
        Prefetch("user__uploads", queryset=avatars, to_attr="avatars"),
    )


def _attachment_node(attachment: Attachment) -> AttachmentNode:
    return AttachmentNode(
        id=ID(str(attachment.id)),
        kind=attachment.kind,
        original_name=attachment.original_name,
        content_type=attachment.content_type,
        size=attachment.size,
        width=attachment.width,
        height=attachment.height,
        content_url=f"/api/attachments/{attachment.id}/content",
    )


def _comment_node(comment: Comment, children: dict[uuid.UUID, list[Comment]]) -> CommentNode:
    prefetched_avatars = getattr(comment.user, "avatars", []) if comment.user_id else []
    avatar = prefetched_avatars[0] if prefetched_avatars else None
    return CommentNode(
        id=ID(str(comment.id)),
        author=AuthorNode(
            user_id=ID(str(comment.user_id)) if comment.user_id else None,
            name=comment.author_name,
            email=comment.author_email,
            homepage=comment.homepage or None,
            avatar_url=f"/api/attachments/{avatar.id}/content" if avatar else None,
        ),
        html_text=comment.html_text,
        text=comment.search_text,
        parent_id=ID(str(comment.parent_id)) if comment.parent_id else None,
        root_id=ID(str(comment.root_id or comment.id)),
        depth=comment.depth,
        score=comment.score,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        attachments=[_attachment_node(item) for item in comment.attachments.all()],
        replies=[_comment_node(item, children) for item in children.get(comment.id, [])],
    )


def _load_branches_sync(keys: list[BranchKey]) -> list[CommentNode | None]:
    if not keys:
        return []
    references = {
        comment_id: root_id or comment_id
        for comment_id, root_id in Comment.objects.filter(
            id__in={key.comment_id for key in keys}
        ).values_list("id", "root_id")
    }
    root_ids = set(references.values())
    max_depth = max(key.depth for key in keys)
    comments = list(
        _comment_queryset()
        .filter(root_id__in=root_ids, depth__lte=max_depth)
        .order_by("created_at", "id")
    )
    by_root: dict[uuid.UUID, list[Comment]] = {}
    for comment in comments:
        by_root.setdefault(comment.root_id or comment.id, []).append(comment)

    results: list[CommentNode | None] = []
    for key in keys:
        root_id = references.get(key.comment_id)
        branch = by_root.get(root_id, []) if root_id else []
        visible = [comment for comment in branch if comment.depth <= key.depth]
        if not visible:
            results.append(None)
            continue
        children: dict[uuid.UUID, list[Comment]] = {}
        for comment in visible:
            if comment.parent_id is not None:
                children.setdefault(comment.parent_id, []).append(comment)
        results.append(_comment_node(visible[0], children))
    return results


async def load_branches(keys: list[BranchKey]) -> list[CommentNode | None]:
    return await database_sync_to_async(_load_branches_sync)(keys)


def branch_loader() -> DataLoader[BranchKey, CommentNode | None]:
    return DataLoader(load_fn=load_branches, max_batch_size=50)


@database_sync_to_async
def root_ids(*, first: int) -> list[uuid.UUID]:
    return list(
        Comment.objects.filter(parent__isnull=True)
        .order_by("-created_at", "-id")
        .values_list("id", flat=True)[:first]
    )
