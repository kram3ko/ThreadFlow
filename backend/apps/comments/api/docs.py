from config.api.docs import ERROR_RESPONSE
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from apps.comments.api.serializers import CommentCreateSerializer, CommentSerializer

COMMENT_EXAMPLE = OpenApiExample(
    "Guest comment",
    value={
        "username": "Alice1",
        "email": "alice@example.com",
        "homepage": "https://example.com",
        "text": "Hello, ThreadFlow",
    },
    request_only=True,
)

TREE_PARAMETERS = [
    OpenApiParameter(
        name="depth",
        type=int,
        location=OpenApiParameter.QUERY,
        description="Maximum reply depth returned, from 0 to 10.",
        required=False,
    ),
]

LIST_PARAMETERS = [
    OpenApiParameter(
        name="sort",
        type=str,
        location=OpenApiParameter.QUERY,
        enum=["date", "name", "email"],
        default="date",
    ),
    OpenApiParameter(
        name="direction",
        type=str,
        location=OpenApiParameter.QUERY,
        enum=["asc", "desc"],
        default="desc",
    ),
    OpenApiParameter(
        name="cursor",
        type=str,
        location=OpenApiParameter.QUERY,
        description="Opaque cursor returned by the previous page.",
        required=False,
    ),
    *TREE_PARAMETERS,
]

document_comment_viewset = extend_schema_view(
    list=extend_schema(
        summary="List comment trees",
        description="Returns 25 cursor-paginated root comments and bounded reply trees.",
        parameters=LIST_PARAMETERS,
        responses={200: CommentSerializer(many=True)},
        tags=["comments"],
    ),
    create=extend_schema(
        summary="Create a root comment",
        request=CommentCreateSerializer,
        responses={
            201: CommentSerializer,
            400: OpenApiResponse(ERROR_RESPONSE, description="Validation failed"),
        },
        examples=[COMMENT_EXAMPLE],
        tags=["comments"],
    ),
    retrieve=extend_schema(
        summary="Get a comment branch",
        parameters=TREE_PARAMETERS,
        responses={
            200: CommentSerializer,
            404: OpenApiResponse(ERROR_RESPONSE, description="Comment not found"),
        },
        tags=["comments"],
    ),
    replies=extend_schema(
        summary="Reply to a comment",
        request=CommentCreateSerializer,
        responses={
            201: CommentSerializer,
            400: OpenApiResponse(ERROR_RESPONSE, description="Validation failed"),
            404: OpenApiResponse(ERROR_RESPONSE, description="Parent comment not found"),
        },
        examples=[COMMENT_EXAMPLE],
        tags=["comments"],
    ),
)
