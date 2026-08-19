import json

import pytest
from apps.captcha.services import issue_challenge
from apps.comments.models import Comment
from apps.comments.realtime.consumer import CommentSocketConsumer
from apps.events.models import OutboxEvent
from asgiref.testing import ApplicationCommunicator
from django.contrib.auth.models import AnonymousUser


def websocket_scope() -> dict:
    return {
        "type": "websocket",
        "asgi": {"version": "3.0"},
        "path": "/ws/comments",
        "raw_path": b"/ws/comments",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 41000),
        "server": ("localhost", 80),
        "subprotocols": [],
        "user": AnonymousUser(),
    }


async def receive_json(communicator: ApplicationCommunicator) -> dict:
    output = await communicator.receive_output(timeout=1)
    return json.loads(output["text"])


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_guest_creates_comment_and_records_live_event():
    communicator = ApplicationCommunicator(CommentSocketConsumer.as_asgi(), websocket_scope())
    await communicator.send_input({"type": "websocket.connect"})
    assert (await communicator.receive_output(timeout=1))["type"] == "websocket.accept"

    await communicator.send_input(
        {
            "type": "websocket.receive",
            "text": json.dumps({"op": "subscribe", "topics": ["comments"]}),
        }
    )
    assert (await receive_json(communicator))["type"] == "subscribed"

    challenge = issue_challenge(answer="ABC123")
    await communicator.send_input(
        {
            "type": "websocket.receive",
            "text": json.dumps(
                {
                    "id": "request-1",
                    "op": "comments.create",
                    "data": {
                        "username": "SocketGuest",
                        "email": "socket@example.com",
                        "homepage": "",
                        "text": "Live <strong>comment</strong>",
                        "captcha_id": str(challenge.id),
                        "captcha_answer": "ABC123",
                    },
                }
            ),
        }
    )

    response = await receive_json(communicator)
    assert response["id"] == "request-1"
    assert response["data"]["comment"]["html_text"] == "Live <strong>comment</strong>"
    assert await Comment.objects.filter(id=response["data"]["comment"]["id"]).aexists()
    assert await OutboxEvent.objects.filter(
        aggregate_id=response["data"]["comment"]["id"]
    ).aexists()

    await communicator.send_input({"type": "websocket.disconnect", "code": 1000})
    await communicator.wait(timeout=1)


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_socket_rejects_unknown_operation():
    communicator = ApplicationCommunicator(CommentSocketConsumer.as_asgi(), websocket_scope())
    await communicator.send_input({"type": "websocket.connect"})
    await communicator.receive_output(timeout=1)
    await communicator.send_input(
        {
            "type": "websocket.receive",
            "text": json.dumps({"id": "request-2", "op": "comments.delete", "data": {}}),
        }
    )

    message = await receive_json(communicator)
    assert message == {
        "type": "error",
        "id": "request-2",
        "code": "unknown_operation",
        "details": "Unknown operation.",
    }

    await communicator.send_input({"type": "websocket.disconnect", "code": 1000})
    await communicator.wait(timeout=1)
