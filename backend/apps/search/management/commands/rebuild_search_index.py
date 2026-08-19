from django.core.management.base import BaseCommand

from apps.comments.models import Comment
from apps.search.documents import ensure_index, index_comment


class Command(BaseCommand):
    help = "Rebuild the comments index from PostgreSQL."

    def handle(self, *args, **options) -> None:
        ensure_index()
        for comment_id in Comment.objects.values_list("id", flat=True).iterator(chunk_size=1000):
            index_comment(str(comment_id))
