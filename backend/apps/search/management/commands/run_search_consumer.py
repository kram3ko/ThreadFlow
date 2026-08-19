from django.core.management.base import BaseCommand

from apps.search.consumers import run_search_consumer


class Command(BaseCommand):
    help = "Consume comment events and update Elasticsearch."

    def handle(self, *args, **options) -> None:
        run_search_consumer()
