# WebSocket contract

ThreadFlow exposes one public realtime endpoint at `/ws/comments`. A valid access cookie attaches the account. Missing, invalid or expired authentication cookies create a guest connection because comment events are public. The handshake origin is validated against Django's allowed hosts.

## Client operations

| Operation | Data | Result |
| --- | --- | --- |
| `subscribe` | `topics: ["comments"]` | Enables public comment events |
| `comments.create` | Comment fields, CAPTCHA fields | Creates a root comment |
| `comments.reply` | Comment fields, CAPTCHA fields, `parent_id` | Creates a reply |

Command envelope:

```json
{
  "id": "7ac9b389-33e7-4e24-9c28-13b621603cef",
  "op": "comments.create",
  "data": {}
}
```

REST creation endpoints remain available as a fallback and call the same validation and persistence service.

## Server messages and events

| Type | Event | Meaning |
| --- | --- | --- |
| `subscribed` | — | Topic subscription accepted |
| `response` | — | Command completed; correlated by `id` |
| `error` | — | Command rejected; contains `code` and `details` |
| `event` | `comment.created` | A root or reply was committed |
| `event` | `comment.voted` | A comment score changed |
| `event` | `search.indexed` | The search projection was updated |

`comment.created` includes a unique `event_id`, `data.kind` (`root` or `reply`) and the public comment representation. Clients deduplicate by comment ID.

## Delivery behavior

The channel layer uses Redis and delivers committed events to connected clients. Comment creation is written to the PostgreSQL outbox and reaches the WebSocket consumer through Kafka. Delivery to an individual browser remains best-effort: after reconnect, the Vue store reloads the authoritative tree through REST. Vote notifications are intentionally best-effort because the score remains authoritative in PostgreSQL and is returned by the vote command.
