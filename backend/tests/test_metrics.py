from unittest.mock import Mock, patch

import pytest
from apps.comments.services import create_comment
from apps.observability.metrics import COMMENTS_CREATED
from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_metrics_endpoint_exposes_prometheus_text():
    response = APIClient().get("/metrics")
    assert response.status_code == 200
    body = response.content.decode()
    assert "threadflow_http_requests_total" in body
    assert "threadflow_events_processed_total" in body


@pytest.mark.django_db(transaction=True)
def test_rolled_back_comment_does_not_increment_metric():
    counter = Mock()
    with (
        patch.object(COMMENTS_CREATED, "labels", return_value=counter),
        patch(
            "apps.attachments.services.claim_attachments",
            side_effect=serializers.ValidationError("invalid attachment"),
        ),
        pytest.raises(serializers.ValidationError),
    ):
        create_comment(
            user=AnonymousUser(),
            author_name="Guest",
            author_email="guest@example.com",
            homepage="",
            text="Comment",
            attachments=[{"id": "unused", "token": "unused"}],
        )

    counter.inc.assert_not_called()
