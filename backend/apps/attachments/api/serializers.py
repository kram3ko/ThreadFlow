from rest_framework import serializers

from apps.attachments.models import Attachment, AttachmentPurpose
from apps.attachments.services import store_upload


class AttachmentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    purpose = serializers.ChoiceField(
        choices=[value.value for value in AttachmentPurpose],
        default=AttachmentPurpose.COMMENT,
    )

    def create(self, validated_data):
        return store_upload(
            upload=validated_data["file"],
            purpose=validated_data["purpose"],
            user=self.context["request"].user,
        )


class AttachmentSerializer(serializers.ModelSerializer):
    content_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = (
            "id",
            "kind",
            "purpose",
            "original_name",
            "content_type",
            "size",
            "width",
            "height",
            "content_url",
            "created_at",
        )

    def get_content_url(self, obj: Attachment) -> str:
        request = self.context.get("request")
        path = f"/api/attachments/{obj.id}/content"
        return request.build_absolute_uri(path) if request else path


class AttachmentUploadResultSerializer(AttachmentSerializer):
    claim_token = serializers.CharField()

    class Meta(AttachmentSerializer.Meta):
        fields = (*AttachmentSerializer.Meta.fields, "claim_token")
