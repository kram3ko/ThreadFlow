from apps.comments.views import (
    CommentDetailView,
    CommentListCreateView,
    CommentReplyCreateView,
)
from django.urls import path

from config.views import health

urlpatterns = [
    path("api/health", health, name="health"),
    path("api/comments", CommentListCreateView.as_view(), name="comment-list-create"),
    path("api/comments/<uuid:comment_id>", CommentDetailView.as_view(), name="comment-detail"),
    path(
        "api/comments/<uuid:comment_id>/replies",
        CommentReplyCreateView.as_view(),
        name="comment-reply",
    ),
]
