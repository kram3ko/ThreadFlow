import uuid
from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User
from apps.comments.models import Comment


class Command(BaseCommand):
    help = "Bulk-create deterministic-shape data for local load tests"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--comments", type=int, default=1_000_000)
        parser.add_argument("--users", type=int, default=10_000)
        parser.add_argument("--root-ratio", type=float, default=0.2)
        parser.add_argument("--batch-size", type=int, default=5_000)

    def handle(self, *args: Any, **options: Any) -> None:
        comment_count = options["comments"]
        user_count = options["users"]
        root_ratio = options["root_ratio"]
        batch_size = options["batch_size"]
        if comment_count < 1 or user_count < 0 or batch_size < 1:
            raise CommandError("comments and batch size must be positive; users cannot be negative")
        if not 0 < root_ratio <= 1:
            raise CommandError("--root-ratio must be greater than zero and at most one")

        users = self._create_users(user_count, batch_size)
        root_count = min(comment_count, max(1, round(comment_count * root_ratio)))
        roots = self._create_roots(root_count, users, batch_size)
        self._create_replies(comment_count - root_count, roots, users, batch_size)
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {comment_count:,} comments "
                f"({root_count:,} roots) and {user_count:,} users"
            )
        )

    def _create_users(self, count: int, batch_size: int) -> list[uuid.UUID]:
        user_ids = [uuid.uuid4() for _ in range(count)]
        users = []
        for user_id in user_ids:
            user = User(
                id=user_id,
                username=f"load_{user_id.hex}",
                email=f"load_{user_id.hex}@example.test",
            )
            user.set_unusable_password()
            users.append(user)
        User.objects.bulk_create(users, batch_size=batch_size)
        return user_ids

    def _create_roots(
        self,
        count: int,
        users: list[uuid.UUID],
        batch_size: int,
    ) -> list[uuid.UUID]:
        root_ids = [uuid.uuid4() for _ in range(count)]
        for offset in range(0, count, batch_size):
            roots = [
                self._comment(
                    comment_id=root_id,
                    root_id=root_id,
                    parent_id=None,
                    depth=0,
                    sequence=index,
                    users=users,
                )
                for index, root_id in enumerate(
                    root_ids[offset : offset + batch_size],
                    start=offset,
                )
            ]
            Comment.objects.bulk_create(roots, batch_size=batch_size)
        return root_ids

    def _create_replies(
        self,
        count: int,
        roots: list[uuid.UUID],
        users: list[uuid.UUID],
        batch_size: int,
    ) -> None:
        replies: list[Comment] = []
        for index in range(count):
            root_id = roots[index % len(roots)]
            replies.append(
                self._comment(
                    comment_id=uuid.uuid4(),
                    root_id=root_id,
                    parent_id=root_id,
                    depth=1,
                    sequence=index + len(roots),
                    users=users,
                )
            )
            if len(replies) == batch_size:
                Comment.objects.bulk_create(replies, batch_size=batch_size)
                replies.clear()
        if replies:
            Comment.objects.bulk_create(replies, batch_size=batch_size)

    @staticmethod
    def _comment(
        *,
        comment_id: uuid.UUID,
        root_id: uuid.UUID,
        parent_id: uuid.UUID | None,
        depth: int,
        sequence: int,
        users: list[uuid.UUID],
    ) -> Comment:
        user_id = users[sequence % len(users)] if users else None
        author = f"LoadUser{sequence % max(len(users), 1):05d}"
        text = f"Load test comment {sequence} about threaded discussions and search"
        return Comment(
            id=comment_id,
            user_id=user_id,
            author_name=author,
            author_email=f"{author.lower()}@example.test",
            homepage="",
            html_text=text,
            search_text=text,
            parent_id=parent_id,
            root_id=root_id,
            depth=depth,
        )
