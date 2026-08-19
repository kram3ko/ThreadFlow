from django.http import FileResponse, Http404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.attachments.api.serializers import AttachmentSerializer, AttachmentUploadSerializer
from apps.attachments.models import Attachment


class AttachmentUploadView(APIView):
    permission_classes = (AllowAny,)
    parser_classes = (MultiPartParser,)

    @extend_schema(request=AttachmentUploadSerializer, responses={201: AttachmentSerializer})
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
        response = FileResponse(file, content_type=attachment.content_type)
        response["Content-Disposition"] = f'inline; filename="{attachment.original_name}"'
        response["X-Content-Type-Options"] = "nosniff"
        if attachment.content_type == "text/plain":
            response["Content-Security-Policy"] = "default-src 'none'"
        return response
