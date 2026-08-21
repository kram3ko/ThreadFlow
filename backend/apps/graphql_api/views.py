from typing import Any

from django.http import HttpRequest, HttpResponse
from strawberry.django.views import AsyncGraphQLView

from apps.graphql_api.schema import context, schema


class ThreadFlowGraphQLView(AsyncGraphQLView):
    async def get_context(self, request: HttpRequest, response: HttpResponse) -> Any:
        return context()


graphql_view = ThreadFlowGraphQLView.as_view(
    schema=schema,
    graphql_ide=None,
    allow_queries_via_get=True,
)
