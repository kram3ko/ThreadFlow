export enum CommentTopic {
  Comments = "comments",
}

export enum CommentOperation {
  Subscribe = "subscribe",
  Create = "comments.create",
  Reply = "comments.reply",
}

export enum CommentEvent {
  Created = "comment.created",
  Voted = "comment.voted",
}

export enum SocketMessageType {
  Response = "response",
  Error = "error",
  Event = "event",
  Subscribed = "subscribed",
}

export type SocketStatus = "connecting" | "open" | "closed";
