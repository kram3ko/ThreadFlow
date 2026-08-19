from rest_framework import serializers


class CaptchaChallengeSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    image_data = serializers.CharField(read_only=True)
    expires_in = serializers.IntegerField(read_only=True)
