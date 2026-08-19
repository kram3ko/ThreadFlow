from typing import Any, cast

from django.urls import path

from apps.comments.realtime.consumer import CommentSocketConsumer

websocket_urlpatterns = [path("ws/comments", cast(Any, CommentSocketConsumer.as_asgi()))]
