from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.search.documents import rebuild_index


class Command(BaseCommand):
    help = "Rebuild the comments index from PostgreSQL."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--batch-size", type=int, default=1_000)

    def handle(self, *args: Any, **options: Any) -> None:
        batch_size = options["batch_size"]
        if batch_size < 1:
            raise CommandError("--batch-size must be positive")
        indexed = rebuild_index(chunk_size=batch_size)
        self.stdout.write(self.style.SUCCESS(f"Indexed {indexed:,} comments"))
