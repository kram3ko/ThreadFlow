from enum import StrEnum


class CommentTopic(StrEnum):
    COMMENTS = "comments"


class CommentOperation(StrEnum):
    SUBSCRIBE = "subscribe"
    CREATE = "comments.create"
    REPLY = "comments.reply"


class CommentEvent(StrEnum):
    CREATED = "comment.created"


class CommentKind(StrEnum):
    ROOT = "root"
    REPLY = "reply"


class SocketMessageType(StrEnum):
    RESPONSE = "response"
    ERROR = "error"
    EVENT = "event"
    SUBSCRIBED = "subscribed"
