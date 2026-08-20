from django.conf import settings
from django.core.management.base import BaseCommand

from apps.observability.server import start_metrics_server
from apps.search.consumers import run_search_consumer


class Command(BaseCommand):
    help = "Consume comment events and update Elasticsearch."

    def handle(self, *args, **options) -> None:
        start_metrics_server(settings.METRICS_PORT)
        run_search_consumer()
