from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.comments.models import Comment
from apps.comments.services import create_comment


class CommentCreateSerializer(serializers.Serializer):
    username = serializers.RegexField(r"^[A-Za-z0-9_]+$", max_length=150, required=False)
    email = serializers.EmailField(required=False)
    homepage = serializers.URLField(required=False, allow_blank=True, default="")
    text = serializers.CharField(max_length=10_000, trim_whitespace=True)

    def validate(self, attrs):
        request = self.context["request"]
        if not request.user.is_authenticated:
            missing = [name for name in ("username", "email") if not attrs.get(name)]
            if missing:
                raise serializers.ValidationError(
                    {name: "This field is required for guests." for name in missing}
                )
        return attrs

    def create(self, validated_data):
        return create_comment(
            user=self.context["request"].user,
            author_name=validated_data.get("username", ""),
            author_email=validated_data.get("email", ""),
            homepage=validated_data["homepage"],
            text=validated_data["text"],
            parent=self.context.get("parent"),
        )


class CommentSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source="search_text", read_only=True)
    replies = serializers.SerializerMethodField()
    has_more_replies = serializers.SerializerMethodField()

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
            "created_at",
            "updated_at",
            "has_more_replies",
            "replies",
        )

    @extend_schema_field({"type": "array", "items": {"$ref": "#/components/schemas/Comment"}})
    def get_replies(self, obj: Comment):
        children = self.context.get("children", {}).get(obj.id, [])
        return CommentSerializer(children, many=True, context=self.context).data

    def get_has_more_replies(self, obj: Comment) -> bool:
        visible_children = self.context.get("children", {}).get(obj.id, [])
        return bool(getattr(obj, "has_replies", False) and not visible_children)
