from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.captcha.api.serializers import CaptchaChallengeSerializer
from apps.captcha.services import issue_challenge


@method_decorator(never_cache, name="dispatch")
class CaptchaChallengeView(APIView):
    authentication_classes: tuple = ()
    permission_classes = (AllowAny,)

    @extend_schema(
        summary="Create a CAPTCHA challenge",
        responses={200: CaptchaChallengeSerializer},
        tags=["captcha"],
    )
    def get(self, request: Request) -> Response:
        challenge = issue_challenge()
        return Response(CaptchaChallengeSerializer(challenge).data)
