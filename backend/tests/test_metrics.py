import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_metrics_endpoint_exposes_prometheus_text():
    response = APIClient().get("/metrics")
    assert response.status_code == 200
    body = response.content.decode()
    assert "threadflow_http_requests_total" in body
    assert "threadflow_events_processed_total" in body
