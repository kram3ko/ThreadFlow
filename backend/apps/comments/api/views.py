from collections import defaultdict
from typing import cast

from django.db.models import Exists, OuterRef, Prefetch, QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.attachments.models import Attachment, AttachmentPurpose
from apps.comments.api.docs import document_comment_viewset
from apps.comments.api.pagination import CommentCursorPagination
from apps.comments.api.serializers import (
    CommentCreateSerializer,
    CommentSerializer,
    PreviewSerializer,
    VoteSerializer,
)
from apps.comments.html import sanitize_comment_html
from apps.comments.models import Comment
from apps.comments.rate_limit import CommentRateThrottle
from apps.comments.realtime.publisher import publish_comment_voted
from apps.comments.voting import apply_vote, voter_identity
from apps.observability.metrics import COMMENT_VOTES


def serialize_tree(roots, descendants):
    children = defaultdict(list)
    for comment in descendants:
        children[comment.parent_id].append(comment)
    for siblings in children.values():
        siblings.sort(key=lambda comment: (comment.created_at, comment.id))
    return CommentSerializer(roots, many=True, context={"children": children}).data


def with_reply_marker(queryset):
    replies = Comment.objects.filter(parent_id=OuterRef("pk"))
    return queryset.annotate(has_replies=Exists(replies))


def with_related_files(queryset):
    avatars = Attachment.objects.filter(purpose=AttachmentPurpose.AVATAR).order_by("-created_at")
    return queryset.select_related("user").prefetch_related(
        "attachments",
        Prefetch("user__uploads", queryset=avatars, to_attr="avatars"),
    )


def requested_depth(request):
    try:
        return min(max(int(request.query_params.get("depth", "2")), 0), 10)
    except ValueError:
        return 2


@document_comment_viewset
class CommentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (AllowAny,)
    pagination_class = CommentCursorPagination
    serializer_class = CommentSerializer
    lookup_value_converter = "uuid"
    queryset = Comment.objects.all()

    def get_throttles(self) -> list[CommentRateThrottle]:
        if self.action not in {"create", "replies"}:
            return []
        return [CommentRateThrottle()]

    def list(self, request, *args, **kwargs):
        roots: QuerySet[Comment] = with_reply_marker(
            with_related_files(self.get_queryset().filter(parent__isnull=True))
        )
        page = cast(list[Comment], self.paginate_queryset(roots))
        root_ids = [comment.id for comment in page]
        descendants = list(
            with_reply_marker(
                with_related_files(
                    self.get_queryset().filter(
                        root_id__in=root_ids,
                        parent__isnull=False,
                        depth__lte=requested_depth(request),
                    )
                )
            )
        )
        return self.get_paginated_response(serialize_tree(page, descendants))

    def create(self, request, *args, **kwargs):
        serializer = CommentCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="preview")
    def preview(self, request, *args, **kwargs):
        serializer = PreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        html, _ = sanitize_comment_html(serializer.validated_data["text"])
        return Response({"html": html})

    @action(detail=True, methods=["post"], url_path="vote")
    def vote(self, request, *args, **kwargs):
        comment = get_object_or_404(self.get_queryset(), id=kwargs["pk"])
        serializer = VoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        score = apply_vote(
            comment=comment,
            identity=voter_identity(request),
            value=serializer.validated_data["value"],
        )
        publish_comment_voted(str(comment.id), score)
        COMMENT_VOTES.inc()
        return Response({"id": str(comment.id), "score": score})

    def retrieve(self, request, *args, **kwargs):
        comment = get_object_or_404(
            with_reply_marker(with_related_files(self.get_queryset())),
            id=kwargs["pk"],
        )
        root_id = comment.root_id or comment.id
        branch = list(
            with_reply_marker(
                with_related_files(
                    self.get_queryset().filter(root_id=root_id, depth__lte=requested_depth(request))
                )
            )
        )
        by_id = {item.id: item for item in branch}
        root = by_id[root_id]
        descendants = [item for item in branch if item.parent_id is not None]
        return Response(serialize_tree([root], descendants)[0])

    @action(detail=True, methods=["post"], url_path="replies")
    def replies(self, request, *args, **kwargs):
        parent = get_object_or_404(
            self.get_queryset().select_related("root"),
            id=kwargs["pk"],
        )
        serializer = CommentCreateSerializer(
            data=request.data,
            context={"request": request, "parent": parent},
        )
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
