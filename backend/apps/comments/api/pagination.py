from typing import ClassVar

from rest_framework.pagination import CursorPagination


class CommentCursorPagination(CursorPagination):
    page_size = 25
    cursor_query_param = "cursor"
    ordering = ("-created_at", "-id")

    ordering_map: ClassVar[dict[tuple[str, str], tuple[str, str]]] = {
        ("date", "asc"): ("created_at", "id"),
        ("date", "desc"): ("-created_at", "-id"),
        ("name", "asc"): ("author_name", "id"),
        ("name", "desc"): ("-author_name", "-id"),
        ("email", "asc"): ("author_email", "id"),
        ("email", "desc"): ("-author_email", "-id"),
    }

    def get_ordering(self, request, queryset, view):
        sort = request.query_params.get("sort", "date")
        direction = request.query_params.get("direction", "desc")
        return self.ordering_map.get((sort, direction), self.ordering)
