import { beforeEach, describe, expect, it, vi } from "vitest";

import { CommentsSocket } from "../src/realtime/commentsSocket";
import { CommentOperation } from "../src/realtime/contracts";

class FakeWebSocket {
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSING = 2;
  static readonly CLOSED = 3;
  static instances: FakeWebSocket[] = [];

  readyState = FakeWebSocket.CONNECTING;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  sent: string[] = [];

  constructor(readonly url: string) {
    FakeWebSocket.instances.push(this);
  }

  open(): void {
    this.readyState = FakeWebSocket.OPEN;
    this.onopen?.();
  }

  send(message: string): void {
    this.sent.push(message);
  }

  close(): void {
    this.readyState = FakeWebSocket.CLOSING;
  }

  finishClose(): void {
    this.readyState = FakeWebSocket.CLOSED;
    this.onclose?.();
  }

  receive(message: object): void {
    this.onmessage?.({ data: JSON.stringify(message) });
  }
}

describe("CommentsSocket", () => {
  beforeEach(() => {
    FakeWebSocket.instances = [];
    vi.stubGlobal("window", { location: { protocol: "http:", host: "threadflow.test" } });
    vi.stubGlobal("WebSocket", FakeWebSocket);
  });

  it("ignores a delayed close event from the replaced connection", async () => {
    const statuses: string[] = [];
    const client = new CommentsSocket(
      () => undefined,
      (status) => statuses.push(status),
      () => undefined,
    );

    client.connect();
    const first = FakeWebSocket.instances[0];
    expect(first).toBeDefined();
    first?.open();

    client.reconnect();
    const second = FakeWebSocket.instances[1];
    expect(second).toBeDefined();
    second?.open();
    first?.finishClose();

    expect(client.isOpen).toBe(true);
    const response = client.request(CommentOperation.Create, { text: "hello" });
    const request = JSON.parse(second?.sent.at(-1) ?? "{}") as { id: string };
    second?.receive({
      type: "response",
      id: request.id,
      data: { comment: { id: "comment-id" } },
    });

    await expect(response).resolves.toMatchObject({ id: request.id });
    expect(statuses.at(-1)).toBe("open");
  });
});
