# Event pipeline

Comment creation writes the `Comment` and `OutboxEvent` rows in one PostgreSQL transaction. The outbox publisher acquires a Redis lock, publishes acknowledged records to Kafka and only then sets `published_at`.

Topics:

| Topic | Purpose |
| --- | --- |
| `comments.created` | Durable comment creation stream |
| `comments.updated` | Reserved for a future comment-editing milestone; not produced now |
| `attachments.uploaded` | Reserved for future asynchronous file processing; not produced now |
| `search.index` | Search-index completion notifications |
| `events.retry` | Consumer-specific retries |
| `events.dlq` | Events that exhausted retry attempts |

`root_id` is the Kafka message key, preserving order within a discussion branch. Search and WebSocket consumers use separate consumer groups. `ProcessedEvent(event_id, consumer_name)` is unique, so retries do not repeat an already completed handler. Elasticsearch uses the comment UUID as its document ID, and WebSocket clients also deduplicate comments by UUID. Unsupported historical outbox records and malformed broker payloads are wrapped with diagnostics and acknowledged only after delivery to `events.dlq`.
