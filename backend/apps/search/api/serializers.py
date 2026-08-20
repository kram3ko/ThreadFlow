from rest_framework import serializers


class SearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, default="", max_length=500)
    author = serializers.CharField(required=False, allow_blank=True, default="", max_length=254)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    sort = serializers.ChoiceField(choices=["relevance", "date"], default="relevance")
    direction = serializers.ChoiceField(choices=["asc", "desc"], default="desc")


class SearchResultSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    text = serializers.CharField()
    author_name = serializers.CharField()
    author_email = serializers.EmailField()
    root_id = serializers.UUIDField()
    created_at = serializers.DateTimeField()
    highlights = serializers.ListField(child=serializers.CharField())


class SearchResponseSerializer(serializers.Serializer):
    results = SearchResultSerializer(many=True)

    def get_fields(self) -> dict[str, serializers.Field]:
        fields = super().get_fields()
        fields["source"] = serializers.ChoiceField(choices=["elasticsearch", "postgresql"])
        return fields
