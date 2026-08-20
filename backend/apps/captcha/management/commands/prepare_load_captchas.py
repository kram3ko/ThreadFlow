import json
from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.captcha.services import store_challenge


class Command(BaseCommand):
    help = "Prepare one-use CAPTCHA credentials for an immediate local k6 run"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--count", type=int, default=1_000)
        parser.add_argument("--answer", default="LOAD42")

    def handle(self, *args: Any, **options: Any) -> None:
        count = options["count"]
        answer = options["answer"]
        if count < 1:
            raise CommandError("--count must be positive")
        if not answer.isalnum() or len(answer) > 12:
            raise CommandError("--answer must contain 1-12 letters or digits")

        credentials = [
            {"id": str(store_challenge(answer=answer)), "answer": answer} for _ in range(count)
        ]
        self.stdout.write(json.dumps(credentials, separators=(",", ":")))
