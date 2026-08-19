from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers

HEALTH_RESPONSE = inline_serializer(
    name="HealthResponse",
    fields={"status": serializers.CharField()},
)

document_health = extend_schema(
    summary="Check service health",
    description="Lightweight liveness check used by Docker and external monitoring.",
    responses={200: HEALTH_RESPONSE},
    examples=[
        OpenApiExample(
            "Healthy service",
            value={"status": "ok"},
            response_only=True,
            status_codes=["200"],
        )
    ],
    tags=["system"],
)
