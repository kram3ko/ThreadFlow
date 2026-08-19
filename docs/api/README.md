# ThreadFlow API

This directory explains API behavior that is broader than a single schema field. The executable contract is generated from DRF serializers and the OpenAPI annotations stored beside each API module.

## Documentation endpoints

| Path | Format | Purpose |
| --- | --- | --- |
| `/api/schema` | OpenAPI 3 | Machine-readable API contract |
| `/api/docs` | Swagger UI | Interactive API explorer |
| `/api/redoc` | ReDoc | Readable API reference |

Swagger and ReDoc assets are bundled locally and served by Nginx from the shared static volume. The documentation does not require a third-party CDN and remains compatible with the application CSP.

## Resources

- [Authentication](authentication.md) — JWT cookies, CSRF and browser session lifecycle.
- [CAPTCHA](captcha.md) — challenge lifecycle and comment submission fields.
- [Comments](comments.md) — tree representation, pagination, sorting and reply behavior.
- Authentication — added with the JWT milestone.
- Attachments — added with the object-storage milestone.
- Search — added with the Elasticsearch milestone.
- GraphQL — added with the read API milestone.
- WebSocket — added with the realtime milestone.

## Documentation rule

Every REST endpoint must include:

1. request and response serializers;
2. OpenAPI summary, parameters, response codes and examples in its `api/docs.py` module;
3. API tests covering success and validation failures;
4. a Markdown update when behavior, workflow or constraints cannot be expressed clearly in OpenAPI.

The Markdown files do not duplicate every schema field. Field-level definitions remain generated from code to prevent documentation drift.
