from prometheus_client import Counter, Histogram

HTTP_REQUESTS = Counter(
    "threadflow_http_requests_total",
    "HTTP requests handled, labeled by method, matched route and status.",
    ["method", "route", "status"],
)
HTTP_REQUEST_DURATION = Histogram(
    "threadflow_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "route"],
)
COMMENTS_CREATED = Counter(
    "threadflow_comments_created_total",
    "Comments created, labeled by root or reply.",
    ["kind"],
)
COMMENT_VOTES = Counter(
    "threadflow_comment_votes_total",
    "Vote requests applied to comments.",
)
SEARCH_QUERIES = Counter(
    "threadflow_search_queries_total",
    "Search requests, labeled by the backend that served them.",
    ["source"],
)
EVENTS_PROCESSED = Counter(
    "threadflow_events_processed_total",
    "Domain events processed by a consumer.",
    ["consumer", "event_type"],
)
EVENTS_PUBLISHED = Counter(
    "threadflow_events_published_total",
    "Outbox events published to Kafka.",
    ["event_type"],
)
