import base64
import hashlib
import hmac
import io
import secrets
import string
import uuid
from dataclasses import dataclass
from enum import StrEnum

from django.conf import settings
from django.core.cache import cache
from PIL import Image, ImageDraw, ImageFont

CAPTCHA_ALPHABET = string.ascii_uppercase + string.digits
CAPTCHA_LENGTH = 6
IMAGE_WIDTH = 190
IMAGE_HEIGHT = 64


@dataclass(frozen=True, slots=True)
class CaptchaChallenge:
    id: uuid.UUID
    image_data: str
    expires_in: int


class CaptchaResult(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    BUSY = "busy"


def _answer_key(challenge_id: uuid.UUID) -> str:
    return f"captcha:{challenge_id}:answer"


def _attempts_key(challenge_id: uuid.UUID) -> str:
    return f"captcha:{challenge_id}:attempts"


def _lock_key(challenge_id: uuid.UUID) -> str:
    return f"captcha:{challenge_id}:lock"


def _answer_digest(challenge_id: uuid.UUID, answer: str) -> str:
    message = f"{challenge_id}:{answer.strip().upper()}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()


def _render_png(answer: str) -> bytes:
    image = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), "#f7f4ec")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=30)

    for _ in range(8):
        coordinates = tuple(
            secrets.randbelow(limit)
            for limit in (IMAGE_WIDTH, IMAGE_HEIGHT, IMAGE_WIDTH, IMAGE_HEIGHT)
        )
        draw.line(coordinates, fill="#b8ad99", width=1)

    for index, character in enumerate(answer):
        x = 15 + index * 27 + secrets.randbelow(5)
        y = 12 + secrets.randbelow(9)
        draw.text((x, y), character, fill="#172033", font=font)

    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def issue_challenge(*, answer: str | None = None) -> CaptchaChallenge:
    challenge_id = uuid.uuid4()
    resolved_answer = answer or "".join(
        secrets.choice(CAPTCHA_ALPHABET) for _ in range(CAPTCHA_LENGTH)
    )
    timeout = settings.CAPTCHA_TTL_SECONDS
    cache.set(_answer_key(challenge_id), _answer_digest(challenge_id, resolved_answer), timeout)
    cache.set(_attempts_key(challenge_id), 0, timeout)
    encoded = base64.b64encode(_render_png(resolved_answer)).decode("ascii")
    return CaptchaChallenge(
        id=challenge_id,
        image_data=f"data:image/png;base64,{encoded}",
        expires_in=timeout,
    )


def verify_challenge(challenge_id: uuid.UUID, answer: str) -> CaptchaResult:
    lock_key = _lock_key(challenge_id)
    if not cache.add(lock_key, 1, timeout=5):
        return CaptchaResult.BUSY

    answer_key = _answer_key(challenge_id)
    attempts_key = _attempts_key(challenge_id)
    try:
        expected = cache.get(answer_key)
        if not isinstance(expected, str):
            return CaptchaResult.EXPIRED

        if hmac.compare_digest(expected, _answer_digest(challenge_id, answer)):
            cache.delete_many((answer_key, attempts_key))
            return CaptchaResult.VALID

        try:
            attempts = cache.incr(attempts_key)
        except ValueError:
            return CaptchaResult.EXPIRED
        if attempts >= settings.CAPTCHA_MAX_ATTEMPTS:
            cache.delete_many((answer_key, attempts_key))
        return CaptchaResult.INVALID
    finally:
        cache.delete(lock_key)
