from dataclasses import asdict

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.observability.metrics import SEARCH_QUERIES
from apps.search.api.serializers import SearchQuerySerializer, SearchResultSerializer
from apps.search.services import search_comments


class SearchView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[SearchQuerySerializer],
        responses={200: SearchResultSerializer(many=True)},
    )
    def get(self, request):
        query = SearchQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        results, source = search_comments(
            query=query.validated_data["q"],
            author=query.validated_data["author"],
            date_from=query.validated_data.get("date_from"),
            date_to=query.validated_data.get("date_to"),
            sort=query.validated_data["sort"],
            direction=query.validated_data["direction"],
        )
        SEARCH_QUERIES.labels(source).inc()
        return Response({"source": source, "results": [asdict(item) for item in results]})
