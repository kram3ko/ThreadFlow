import json
import uuid

import pytest
from apps.accounts.models import User
from apps.captcha.services import CaptchaResult, verify_challenge
from apps.comments.models import Comment
from apps.events.models import OutboxEvent
from django.core.management import call_command


@pytest.mark.django_db
def test_seed_load_data_creates_consistent_tree(capsys):
    call_command("seed_load_data", comments=12, users=3, root_ratio=0.25, batch_size=4)

    assert User.objects.count() == 3
    assert Comment.objects.filter(parent__isnull=True).count() == 3
    assert Comment.objects.filter(parent__isnull=False, depth=1).count() == 9
    root_ids = Comment.objects.filter(depth=0).values_list("id", flat=True)
    assert not Comment.objects.exclude(root_id__in=root_ids).exists()
    assert OutboxEvent.objects.count() == 0
    assert "Created 12 comments" in capsys.readouterr().out


def test_prepare_load_captchas_outputs_valid_one_use_credentials(capsys):
    call_command("prepare_load_captchas", count=2, answer="LOAD42")
    credentials = json.loads(capsys.readouterr().out)

    assert len(credentials) == 2
    first = credentials[0]
    challenge_id = uuid.UUID(first["id"])
    assert verify_challenge(challenge_id, first["answer"]) is CaptchaResult.VALID
    assert verify_challenge(challenge_id, first["answer"]) is CaptchaResult.EXPIRED
