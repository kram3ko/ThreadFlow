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

Guest requests must provide `username` and `email`. Authenticated requests derive both values from the account snapshot. `homepage` is optional. Every request must also provide a fresh `captcha_id` and `captcha_answer` from `GET /api/captcha`.

## Text safety

Comment HTML is restricted to `<a href="" title="">`, `<code>`, `<i>` and `<strong>`. Allowed formatting tags must be balanced; unsafe elements, attributes and URL schemes are removed with `nh3` before storage. Links receive `rel="nofollow noopener noreferrer"`. Vue renders only the backend-produced `html_text` field.

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
