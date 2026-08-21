from typing import Any

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.captcha.services import CaptchaResult, verify_challenge
from apps.comments.html import sanitize_comment_html
from apps.comments.models import Comment
from apps.comments.services import create_comment


class AttachmentClaimSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    token = serializers.CharField(max_length=64)


class VoteSerializer(serializers.Serializer):
    value = serializers.ChoiceField(choices=[-1, 0, 1])


class VoteResultSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    score = serializers.IntegerField()


class PreviewSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=10_000, trim_whitespace=False)


class PreviewResultSerializer(serializers.Serializer):
    html = serializers.CharField()


class CommentCreateSerializer(serializers.Serializer):
    username = serializers.RegexField(
        r"^[A-Za-z0-9_]+$", max_length=150, required=False, allow_blank=True
    )
    email = serializers.EmailField(required=False, allow_blank=True)
    homepage = serializers.URLField(required=False, allow_blank=True, default="")
    text = serializers.CharField(max_length=10_000, trim_whitespace=True)
    captcha_id = serializers.UUIDField(write_only=True)
    captcha_answer = serializers.RegexField(
        r"^[A-Za-z0-9]+$", max_length=12, write_only=True, trim_whitespace=True
    )
    attachments = AttachmentClaimSerializer(many=True, required=False)

    def validate_text(self, value: str) -> str:
        sanitize_comment_html(value)
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        request = self.context["request"]
        if not request.user.is_authenticated:
            missing = [name for name in ("username", "email") if not attrs.get(name)]
            if missing:
                raise serializers.ValidationError(
                    {name: "This field is required for guests." for name in missing}
                )
        if len(attrs.get("attachments", [])) > 4:
            raise serializers.ValidationError(
                {"attachments": "A comment can contain at most four attachments."}
            )
        result = verify_challenge(attrs["captcha_id"], attrs["captcha_answer"])
        if result is not CaptchaResult.VALID:
            message = {
                CaptchaResult.INVALID: "CAPTCHA answer is incorrect.",
                CaptchaResult.EXPIRED: "CAPTCHA challenge has expired.",
                CaptchaResult.BUSY: "CAPTCHA challenge is already being checked.",
            }[result]
            raise serializers.ValidationError({"captcha_answer": message})
        attrs.pop("captcha_id")
        attrs.pop("captcha_answer")
        return attrs

    def create(self, validated_data: dict[str, Any]) -> Comment:
        return create_comment(
            user=self.context["request"].user,
            author_name=validated_data.get("username", ""),
            author_email=validated_data.get("email", ""),
            homepage=validated_data["homepage"],
            text=validated_data["text"],
            parent=self.context.get("parent"),
            attachments=validated_data.get("attachments", []),
        )


class CommentSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source="search_text", read_only=True)
    replies = serializers.SerializerMethodField()
    has_more_replies = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            "id",
            "author_name",
            "author_email",
            "homepage",
            "html_text",
            "text",
            "parent_id",
            "root_id",
            "depth",
            "score",
            "created_at",
            "updated_at",
            "has_more_replies",
            "avatar_url",
            "attachments",
            "replies",
        )

    @extend_schema_field({"type": "array", "items": {"$ref": "#/components/schemas/Comment"}})
    def get_replies(self, obj: Comment) -> Any:
        children = self.context.get("children", {}).get(obj.id, [])
        return CommentSerializer(children, many=True, context=self.context).data

    def get_has_more_replies(self, obj: Comment) -> bool:
        visible_children = self.context.get("children", {}).get(obj.id, [])
        return bool(getattr(obj, "has_replies", False) and not visible_children)

    def get_attachments(self, obj: Comment) -> Any:
        from apps.attachments.api.serializers import AttachmentSerializer

        return AttachmentSerializer(
            obj.attachments.all(), many=True, context={"request": self.context.get("request")}
        ).data

    def get_avatar_url(self, obj: Comment) -> str | None:
        if not obj.user_id:
            return None
        from apps.attachments.models import AttachmentPurpose

        prefetched = getattr(obj.user, "avatars", None)
        if prefetched is not None:
            avatar = prefetched[0] if prefetched else None
        else:
            avatar = (
                obj.user.uploads.filter(purpose=AttachmentPurpose.AVATAR)
                .order_by("-created_at")
                .first()
            )
        return f"/api/attachments/{avatar.id}/content" if avatar else None
