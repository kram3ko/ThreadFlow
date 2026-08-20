# Attachments

`POST /api/attachments` accepts multipart form data with `file` and `purpose`. Comment uploads return an opaque `claim_token`; pass the returned `id` and token in the comment command's `attachments` array. The token is consumed when PostgreSQL atomically links the object to the comment.

Supported content is detected from bytes, not the filename: JPG, PNG, GIF and UTF-8 TXT. Images are proportionally reduced to 320×240, TXT is limited to 100 KB, and all objects receive random storage keys. `GET /api/attachments/{id}/content` serves private objects through Django with `nosniff`; text responses also receive a restrictive CSP.

Authenticated users may upload an image with `purpose=avatar`. The newest avatar is returned on the user and comment DTOs. Guests retain deterministic initial avatars.
