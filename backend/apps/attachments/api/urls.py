from django.urls import path

from apps.attachments.api.views import AttachmentContentView, AttachmentUploadView

urlpatterns = [
    path("attachments", AttachmentUploadView.as_view(), name="attachment-upload"),
    path(
        "attachments/<uuid:pk>/content",
        AttachmentContentView.as_view(),
        name="attachment-content",
    ),
]
