from django.http import FileResponse, Http404
from django.utils.http import content_disposition_header
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.attachments.api.serializers import (
    AttachmentSerializer,
    AttachmentUploadResultSerializer,
    AttachmentUploadSerializer,
)
from apps.attachments.models import Attachment


class AttachmentUploadView(APIView):
    permission_classes = (AllowAny,)
    parser_classes = (MultiPartParser,)

    @extend_schema(
        request=AttachmentUploadSerializer,
        responses={201: AttachmentUploadResultSerializer},
    )
    def post(self, request):
        serializer = AttachmentUploadSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        stored = serializer.save()
        data = AttachmentSerializer(stored.attachment, context={"request": request}).data
        data["claim_token"] = stored.claim_token
        return Response(data, status=status.HTTP_201_CREATED)


class AttachmentContentView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(responses={(200, "application/octet-stream"): bytes})
    def get(self, request, pk):
        try:
            attachment = Attachment.objects.get(id=pk)
            file = attachment.file.open("rb")
        except (Attachment.DoesNotExist, OSError) as exc:
            raise Http404 from exc
        content_type = attachment.content_type
        if content_type == "text/plain":
            content_type = "text/plain; charset=utf-8"
        response = FileResponse(file, content_type=content_type)
        disposition = content_disposition_header(
            as_attachment=False, filename=attachment.original_name
        )
        if disposition:
            response["Content-Disposition"] = disposition
        response["X-Content-Type-Options"] = "nosniff"
        if attachment.content_type == "text/plain":
            response["Content-Security-Policy"] = "default-src 'none'"
        return response
