# Comments API

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/comments` | List root comments and bounded reply trees |
| `POST` | `/api/comments` | Create a root comment |
| `GET` | `/api/comments/{id}` | Return the complete root branch up to requested depth |
| `POST` | `/api/comments/{id}/replies` | Reply to any existing comment |

The URL identifier is a UUID. Routes intentionally have no trailing slash.

## Tree representation

Each comment contains:

- `parent_id`, which identifies its direct parent;
- `root_id`, which groups all comments belonging to one branch;
- `depth`, where a root is `0`;
- `replies`, containing visible direct children;
- `has_more_replies`, indicating children hidden by the depth limit.

Logical nesting is not limited when comments are written. API responses accept `depth=0..10` and default to two reply levels so a pathological branch cannot create an unbounded response.

## Root pagination

`GET /api/comments` paginates root comments in pages of 25. Replies do not consume root-page slots. The response contains opaque `next` and `previous` cursor URLs.

Supported ordering:

| Parameter | Values | Default |
| --- | --- | --- |
| `sort` | `date`, `name`, `email` | `date` |
| `direction` | `asc`, `desc` | `desc` |

The UUID is the deterministic tie-breaker for every cursor ordering. Clients must treat the cursor as opaque and must not construct it manually.

## Guest identity

Until JWT authentication is implemented, `username` and `email` are required for every created comment. `homepage` is optional. Registered users will later receive author values from their account rather than request data.

## Text safety

The foundation milestone escapes all submitted text before exposing `html_text`. The later sanitization milestone will allow only the documented subset of HTML using `nh3`. Vue must render only backend-sanitized HTML.

## Error format

Validation and lookup failures use the shared envelope:

```json
{
  "error": {
    "code": "invalid",
    "details": {}
  }
}
```
