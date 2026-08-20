from django.conf import settings
from django.core.management.base import BaseCommand

from apps.comments.realtime.kafka_consumer import run_websocket_consumer
from apps.observability.server import start_metrics_server


class Command(BaseCommand):
    help = "Consume domain events and deliver them through Channels."

    def handle(self, *args, **options) -> None:
        start_metrics_server(settings.METRICS_PORT)
        run_websocket_consumer()
