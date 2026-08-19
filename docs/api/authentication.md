# Authentication API

ThreadFlow uses short-lived access JWTs and rotating refresh JWTs. Both tokens are stored in
`httpOnly` cookies and are never returned in response bodies or exposed to Vue application state.

## Browser flow

1. `GET /api/auth/csrf` initializes the readable CSRF cookie.
2. The SPA sends its value in `X-CSRFToken` for unsafe requests.
3. Registration or login sets access and refresh cookies.
4. `GET /api/auth/me` restores the current user without exposing a token.
5. `POST /api/auth/refresh` replaces an expired access token and rotates the refresh token.
6. `POST /api/auth/logout` expires both cookies in the browser.

The access cookie is available to the complete API. The refresh cookie is restricted to
`/api/auth`, reducing where the browser sends the longer-lived credential.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/auth/csrf` | Initialize CSRF protection |
| `POST` | `/api/auth/register` | Create an account and sign in |
| `POST` | `/api/auth/login` | Sign in with username and password |
| `POST` | `/api/auth/refresh` | Rotate JWT cookies |
| `POST` | `/api/auth/logout` | Expire JWT cookies |
| `GET` | `/api/auth/me` | Return the current authenticated user |

Registered users do not submit author identity with comments. Django copies username and email
from the authenticated account into immutable comment snapshots.

Logout currently invalidates the browser session by expiring its cookies. Server-side refresh-token
revocation will be added with the Redis token registry milestone.
