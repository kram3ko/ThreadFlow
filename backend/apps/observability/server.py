from prometheus_client import start_http_server


def start_metrics_server(port: int) -> None:
    """Expose Prometheus metrics for a long-running consumer process."""
    start_http_server(port)
