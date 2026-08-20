import uuid
from dataclasses import dataclass
from typing import Any, cast

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers

from apps.accounts.models import User
from apps.comments.api.serializers import CommentCreateSerializer
from apps.comments.models import Comment
from apps.comments.rate_limit import check_comment_rate_limit
from apps.comments.realtime.contracts import (
    CommentOperation,
    CommentTopic,
    SocketMessageType,
)
from apps.comments.realtime.publisher import PUBLIC_COMMENT_GROUP, comment_payload


@dataclass(frozen=True, slots=True)
class _RequestContext:
    user: User | AnonymousUser


class CommentSocketConsumer(AsyncJsonWebsocketConsumer):
    subscribed = False

    async def connect(self) -> None:
        await self.accept()

    async def disconnect(self, code: int) -> None:
        if self.subscribed:
            await self.channel_layer.group_discard(PUBLIC_COMMENT_GROUP, self.channel_name)

    async def receive_json(self, content: Any, **kwargs: Any) -> None:
        if not isinstance(content, dict):
            await self._error(None, "bad_envelope", "Message must be a JSON object.")
            return

        operation = content.get("op")
        if operation == CommentOperation.SUBSCRIBE:
            await self._subscribe(content)
            return
        if operation not in {CommentOperation.CREATE, CommentOperation.REPLY}:
            await self._error(content.get("id"), "unknown_operation", "Unknown operation.")
            return
        await self._create(content, reply=operation == CommentOperation.REPLY)

    async def _subscribe(self, content: dict[str, Any]) -> None:
        topics = content.get("topics")
        if topics != [CommentTopic.COMMENTS]:
            await self._error(content.get("id"), "invalid_topics", "Only comments is available.")
            return
        if not self.subscribed:
            await self.channel_layer.group_add(PUBLIC_COMMENT_GROUP, self.channel_name)
            self.subscribed = True
        await self.send_json(
            {"type": SocketMessageType.SUBSCRIBED, "topics": [CommentTopic.COMMENTS]}
        )

    async def _create(self, content: dict[str, Any], *, reply: bool) -> None:
        request_id = content.get("id")
        data = content.get("data")
        if not isinstance(request_id, str) or not isinstance(data, dict):
            await self._error(request_id, "bad_envelope", "id and data are required.")
            return

        payload = dict(data)
        parent_id = payload.pop("parent_id", None) if reply else None
        if reply and not isinstance(parent_id, str):
            await self._error(request_id, "invalid", {"parent_id": ["This field is required."]})
            return

        try:
            comment = await _create_comment(
                payload=payload,
                parent_id=parent_id,
                user=self._user(),
                identity=self._identity(),
            )
        except serializers.ValidationError as exc:
            await self._error(request_id, "invalid", exc.detail)
            return
        except Comment.DoesNotExist:
            await self._error(request_id, "not_found", {"parent_id": ["Comment not found."]})
            return
        except ValueError:
            await self._error(request_id, "invalid", {"parent_id": ["Invalid UUID."]})
            return

        await self.send_json(
            {
                "type": SocketMessageType.RESPONSE,
                "id": request_id,
                "data": {"comment": comment},
            }
        )

    def _identity(self) -> str:
        user = self._user()
        if user.is_authenticated:
            return f"user:{user.pk}"
        client = self.scope.get("client")
        host = client[0] if isinstance(client, tuple) and client else "unknown"
        return f"guest:{host}"

    def _user(self) -> User | AnonymousUser:
        return cast(User | AnonymousUser, self.scope.get("user", AnonymousUser()))

    async def comment_created(self, event: dict[str, Any]) -> None:
        await self.send_json(event["envelope"])

    async def comment_voted(self, event: dict[str, Any]) -> None:
        await self.send_json(event["envelope"])

    async def search_indexed(self, event: dict[str, Any]) -> None:
        await self.send_json(event["envelope"])

    async def _error(self, request_id: Any, code: str, details: Any) -> None:
        await self.send_json(
            {
                "type": SocketMessageType.ERROR,
                "id": request_id,
                "code": code,
                "details": details,
            }
        )


@database_sync_to_async
def _create_comment(
    *,
    payload: dict[str, Any],
    parent_id: str | None,
    user: User | AnonymousUser,
    identity: str,
) -> dict[str, Any]:
    limit = check_comment_rate_limit(identity)
    if not limit.allowed:
        raise serializers.ValidationError(
            {"rate_limit": [f"Try again in {limit.retry_after} seconds."]}
        )
    parent = (
        Comment.objects.select_related("root").get(id=uuid.UUID(parent_id)) if parent_id else None
    )
    serializer = CommentCreateSerializer(
        data=payload,
        context={"request": _RequestContext(user=user), "parent": parent},
    )
    serializer.is_valid(raise_exception=True)
    return comment_payload(serializer.save())
