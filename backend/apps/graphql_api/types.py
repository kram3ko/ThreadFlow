from datetime import datetime
from typing import Annotated

import strawberry


@strawberry.type
class AttachmentNode:
    id: strawberry.ID
    kind: str
    original_name: str
    content_type: str
    size: int
    width: int | None
    height: int | None
    content_url: str


@strawberry.type
class AuthorNode:
    user_id: strawberry.ID | None
    name: str
    email: str
    homepage: str | None
    avatar_url: str | None


@strawberry.type
class CommentNode:
    id: strawberry.ID
    author: AuthorNode
    html_text: str
    text: str
    parent_id: strawberry.ID | None
    root_id: strawberry.ID
    depth: int
    score: int
    created_at: datetime
    updated_at: datetime
    attachments: list[AttachmentNode]
    replies: list[Annotated["CommentNode", strawberry.lazy("apps.graphql_api.types")]]
