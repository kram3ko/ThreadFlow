import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

import orjson


class EventType(StrEnum):
    COMMENT_CREATED = "comments.created"
    SEARCH_INDEXED = "search.index"


class ConsumerName(StrEnum):
    SEARCH = "search"
    WEBSOCKET = "websocket"


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    event_id: str
    event_type: str
    aggregate_id: str
    occurred_at: str
    payload: dict[str, Any]
    attempt: int = 0
    target_consumer: str | None = None

    def encode(self) -> bytes:
        return orjson.dumps(asdict(self))

    @classmethod
    def decode(cls, value: bytes) -> EventEnvelope:
        data = orjson.loads(value)
        return cls(**data)

    @classmethod
    def create(
        cls,
        *,
        event_id: uuid.UUID,
        event_type: str,
        aggregate_id: uuid.UUID,
        occurred_at: datetime,
        payload: dict[str, Any],
    ) -> EventEnvelope:
        return cls(
            event_id=str(event_id),
            event_type=event_type,
            aggregate_id=str(aggregate_id),
            occurred_at=occurred_at.isoformat(),
            payload=payload,
        )
