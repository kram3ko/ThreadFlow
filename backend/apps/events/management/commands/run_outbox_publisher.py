import time

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.events.publisher import publish_pending_batch
from apps.observability.server import start_metrics_server


class Command(BaseCommand):
    help = "Publish pending transactional outbox events to Kafka."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options) -> None:
        if not options["once"]:
            start_metrics_server(settings.METRICS_PORT)
        while True:
            publish_pending_batch()
            if options["once"]:
                return
            time.sleep(settings.OUTBOX_POLL_INTERVAL_SECONDS)
