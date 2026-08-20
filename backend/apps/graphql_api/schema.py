import uuid
from dataclasses import dataclass

import strawberry
from graphql import GraphQLError
from strawberry.dataloader import DataLoader
from strawberry.extensions import MaxAliasesLimiter, MaxTokensLimiter, QueryDepthLimiter
from strawberry.types import Info

from apps.graphql_api.loaders import BranchKey, branch_loader, root_ids
from apps.graphql_api.types import CommentNode

MAX_BRANCH_DEPTH = 10
MAX_BRANCHES = 25


@dataclass(slots=True)
class GraphQLContext:
    branches: DataLoader[BranchKey, CommentNode | None]


def context() -> GraphQLContext:
    return GraphQLContext(branches=branch_loader())


def validate_depth(depth: int) -> int:
    if depth < 0 or depth > MAX_BRANCH_DEPTH:
        raise GraphQLError(f"depth must be between 0 and {MAX_BRANCH_DEPTH}")
    return depth


def branch_key(comment_id: strawberry.ID, depth: int) -> BranchKey:
    validate_depth(depth)
    try:
        parsed_id = uuid.UUID(str(comment_id))
    except ValueError as exc:
        raise GraphQLError("comment ID must be a UUID") from exc
    return BranchKey(comment_id=parsed_id, depth=depth)


@strawberry.type
class Query:
    @strawberry.field
    async def comment_branch(
        self,
        info: Info[GraphQLContext, None],
        id: strawberry.ID,
        depth: int = 3,
    ) -> CommentNode | None:
        return await info.context.branches.load(branch_key(id, depth))

    @strawberry.field
    async def comment_branches(
        self,
        info: Info[GraphQLContext, None],
        ids: list[strawberry.ID],
        depth: int = 3,
    ) -> list[CommentNode]:
        if len(ids) > MAX_BRANCHES:
            raise GraphQLError(f"at most {MAX_BRANCHES} branches can be requested")
        branches = await info.context.branches.load_many([branch_key(id, depth) for id in ids])
        return [branch for branch in branches if branch is not None]

    @strawberry.field
    async def root_comments(
        self,
        info: Info[GraphQLContext, None],
        first: int = 25,
        depth: int = 2,
    ) -> list[CommentNode]:
        if first < 1 or first > MAX_BRANCHES:
            raise GraphQLError(f"first must be between 1 and {MAX_BRANCHES}")
        validate_depth(depth)
        keys = [BranchKey(comment_id=id, depth=depth) for id in await root_ids(first=first)]
        branches = await info.context.branches.load_many(keys)
        return [branch for branch in branches if branch is not None]


schema = strawberry.Schema(
    query=Query,
    extensions=[
        lambda: QueryDepthLimiter(max_depth=12),
        lambda: MaxAliasesLimiter(max_alias_count=25),
        lambda: MaxTokensLimiter(max_token_count=5000),
    ],
)
