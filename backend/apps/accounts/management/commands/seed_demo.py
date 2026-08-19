import os

from django.core.management.base import BaseCommand

from apps.accounts.models import User


class Command(BaseCommand):
    help = "Create or update the local demo user"

    def handle(self, *args, **options):
        password = os.getenv("DEMO_USER_PASSWORD")
        if not password:
            self.stdout.write("DEMO_USER_PASSWORD is not set; demo user was not created")
            return

        username = os.getenv("DEMO_USER_NAME", "demo")
        email = os.getenv("DEMO_USER_EMAIL", "demo@threadflow.local")
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )
        user.email = email
        user.set_password(password)
        user.save(update_fields=["email", "password"])
        self.stdout.write(self.style.SUCCESS(f"Demo user '{username}' is ready"))
