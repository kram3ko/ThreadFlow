from collections import defaultdict

from django.db.models import Exists, OuterRef, QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comments.models import Comment
from apps.comments.pagination import CommentCursorPagination
from apps.comments.serializers import CommentCreateSerializer, CommentSerializer


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


def requested_depth(request):
    try:
        return min(max(int(request.query_params.get("depth", "2")), 0), 10)
    except ValueError:
        return 2


class CommentListCreateView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        roots: QuerySet[Comment] = with_reply_marker(
            Comment.objects.filter(parent__isnull=True).select_related("user")
        )
        paginator = CommentCursorPagination()
        page = paginator.paginate_queryset(roots, request, view=self)
        assert page is not None
        root_ids = [comment.id for comment in page]
        descendants = list(
            with_reply_marker(
                Comment.objects.filter(
                    root_id__in=root_ids,
                    parent__isnull=False,
                    depth__lte=requested_depth(request),
                ).select_related("user")
            )
        )
        return paginator.get_paginated_response(serialize_tree(page, descendants))

    def post(self, request):
        serializer = CommentCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class CommentDetailView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, comment_id):
        comment = get_object_or_404(
            with_reply_marker(Comment.objects.select_related("user")), id=comment_id
        )
        root_id = comment.root_id or comment.id
        branch = list(
            with_reply_marker(
                Comment.objects.filter(
                    root_id=root_id,
                    depth__lte=requested_depth(request),
                ).select_related("user")
            )
        )
        by_id = {item.id: item for item in branch}
        root = by_id[root_id]
        descendants = [item for item in branch if item.parent_id is not None]
        return Response(serialize_tree([root], descendants)[0])


class CommentReplyCreateView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, comment_id):
        parent = get_object_or_404(Comment.objects.select_related("root"), id=comment_id)
        serializer = CommentCreateSerializer(
            data=request.data,
            context={"request": request, "parent": parent},
        )
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
