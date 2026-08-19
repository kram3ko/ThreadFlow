# CAPTCHA API

`GET /api/captcha` creates a short-lived challenge and returns its UUID, expiry and a PNG data URL. Responses are marked `no-store`.

Every root comment and reply must include `captcha_id` and `captcha_answer`. Answers are normalized to uppercase and compared against an HMAC digest stored in Redis. A successful challenge is consumed; failed challenges expire after the configured number of attempts or TTL.

```json
{
  "id": "bd452430-f18d-4f5f-a933-18fc48ed2f2b",
  "image_data": "data:image/png;base64,...",
  "expires_in": 300
}
```
