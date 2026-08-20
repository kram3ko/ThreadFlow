from django.core.management.base import BaseCommand

from apps.comments.realtime.kafka_consumer import run_websocket_consumer


class Command(BaseCommand):
    help = "Consume domain events and deliver them through Channels."

    def handle(self, *args, **options) -> None:
        run_websocket_consumer()
