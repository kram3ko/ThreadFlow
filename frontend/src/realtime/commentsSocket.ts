import {
  CommentEvent,
  CommentOperation,
  CommentTopic,
  SocketMessageType,
  type SocketStatus,
} from "./contracts";
import type { CommentItem } from "../types";

interface CommentCreatedEvent {
  type: SocketMessageType.Event;
  event: CommentEvent.Created;
  event_id: string;
  data: { kind: "root" | "reply"; comment: CommentItem };
}

interface CommentVotedEvent {
  type: SocketMessageType.Event;
  event: CommentEvent.Voted;
  event_id: string;
  data: { comment_id: string; score: number };
}

interface ResponseMessage {
  type: SocketMessageType.Response;
  id: string;
  data: { comment: CommentItem };
}

interface ErrorMessage {
  type: SocketMessageType.Error;
  id: string | null;
  code: string;
  details: unknown;
}

type SocketMessage =
  | CommentCreatedEvent
  | CommentVotedEvent
  | ResponseMessage
  | ErrorMessage
  | { type: SocketMessageType.Subscribed; topics: CommentTopic[] };

interface PendingRequest {
  resolve: (message: ResponseMessage) => void;
  reject: (error: SocketCommandError) => void;
  timeout: ReturnType<typeof setTimeout>;
}

export class SocketCommandError extends Error {
  constructor(
    readonly code: string,
    readonly details: unknown,
  ) {
    super(typeof details === "string" ? details : code);
    this.name = "SocketCommandError";
  }
}

const BACKOFF_MS = [1_000, 2_000, 5_000, 10_000, 30_000] as const;
const REQUEST_TIMEOUT_MS = 15_000;

function requestId(): string {
  if (globalThis.crypto.randomUUID) return globalThis.crypto.randomUUID();
  const bytes = globalThis.crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = ((bytes[6] ?? 0) & 0x0f) | 0x40;
  bytes[8] = ((bytes[8] ?? 0) & 0x3f) | 0x80;
  const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

export class CommentsSocket {
  #socket: WebSocket | null = null;
  #pending = new Map<string, PendingRequest>();
  #reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  #reconnectAttempt = 0;
  #closedManually = false;

  constructor(
    private readonly onComment: (comment: CommentItem) => void,
    private readonly onStatus: (status: SocketStatus) => void,
    private readonly onVote: (commentId: string, score: number) => void,
  ) {}

  get isOpen(): boolean {
    return this.#socket?.readyState === WebSocket.OPEN;
  }

  connect(): void {
    if (this.#socket && this.#socket.readyState <= WebSocket.OPEN) return;
    this.#closedManually = false;
    this.onStatus("connecting");
    const scheme = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${scheme}://${window.location.host}/ws/comments`);
    socket.onopen = () => this.#onOpen(socket);
    socket.onmessage = (event: MessageEvent<string>) => {
      if (this.#socket === socket) this.#onMessage(event.data);
    };
    socket.onclose = () => this.#onClose(socket);
    socket.onerror = () => socket.close();
    this.#socket = socket;
  }

  reconnect(): void {
    this.close();
    this.#closedManually = false;
    this.connect();
  }

  close(): void {
    this.#closedManually = true;
    if (this.#reconnectTimer) clearTimeout(this.#reconnectTimer);
    this.#reconnectTimer = null;
    this.#socket?.close();
    this.#socket = null;
    this.#rejectPending("disconnected", "Connection closed.");
    this.onStatus("closed");
  }

  request(operation: CommentOperation.Create | CommentOperation.Reply, data: object) {
    const socket = this.#socket;
    if (!this.isOpen || !socket) {
      return Promise.reject(new SocketCommandError("not_connected", "Connection is not open."));
    }
    const id = requestId();
    return new Promise<ResponseMessage>((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.#pending.delete(id);
        reject(new SocketCommandError("timeout", "The server did not respond in time."));
      }, REQUEST_TIMEOUT_MS);
      this.#pending.set(id, { resolve, reject, timeout });
      try {
        socket.send(JSON.stringify({ id, op: operation, data }));
      } catch {
        clearTimeout(timeout);
        this.#pending.delete(id);
        reject(new SocketCommandError("send_failed", "Unable to send the command."));
      }
    });
  }

  #onOpen(socket: WebSocket): void {
    if (this.#socket !== socket) return;
    this.#reconnectAttempt = 0;
    this.onStatus("open");
    socket.send(
      JSON.stringify({ op: CommentOperation.Subscribe, topics: [CommentTopic.Comments] }),
    );
  }

  #onMessage(raw: string): void {
    let message: SocketMessage;
    try {
      message = JSON.parse(raw) as SocketMessage;
    } catch {
      return;
    }
    if (message.type === SocketMessageType.Event && message.event === CommentEvent.Created) {
      this.onComment(message.data.comment);
      return;
    }
    if (message.type === SocketMessageType.Event && message.event === CommentEvent.Voted) {
      this.onVote(message.data.comment_id, message.data.score);
      return;
    }
    if (message.type === SocketMessageType.Response) {
      const pending = this.#pending.get(message.id);
      if (!pending) return;
      clearTimeout(pending.timeout);
      this.#pending.delete(message.id);
      pending.resolve(message);
      return;
    }
    if (message.type === SocketMessageType.Error && message.id) {
      const pending = this.#pending.get(message.id);
      if (!pending) return;
      clearTimeout(pending.timeout);
      this.#pending.delete(message.id);
      pending.reject(new SocketCommandError(message.code, message.details));
    }
  }

  #onClose(socket: WebSocket): void {
    if (this.#socket !== socket) return;
    this.#socket = null;
    this.onStatus("closed");
    this.#rejectPending("disconnected", "Connection was interrupted.");
    if (this.#closedManually) return;
    const delay = BACKOFF_MS[Math.min(this.#reconnectAttempt, BACKOFF_MS.length - 1)] ?? 30_000;
    this.#reconnectAttempt += 1;
    this.#reconnectTimer = setTimeout(() => this.connect(), delay);
  }

  #rejectPending(code: string, details: string): void {
    for (const pending of this.#pending.values()) {
      clearTimeout(pending.timeout);
      pending.reject(new SocketCommandError(code, details));
    }
    this.#pending.clear();
  }
}
