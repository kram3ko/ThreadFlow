import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "../src/api";
import { useCommentsStore } from "../src/stores/comments";
import type { CommentItem, CommentPage } from "../src/types";

vi.mock("../src/api", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const emptyPage: CommentPage = {
  next: null,
  previous: null,
  results: [],
};

describe("comments store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("loads comments with the selected ordering", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: emptyPage });
    const store = useCommentsStore();

    await store.load("name", "asc");

    expect(api.get).toHaveBeenCalledWith("/comments", {
      params: { sort: "name", direction: "asc" },
    });
    expect(store.comments).toEqual([]);
    expect(store.loading).toBe(false);
  });

  it("creates a reply and reloads the tree", async () => {
    vi.mocked(api.post).mockResolvedValue({ data: {} });
    vi.mocked(api.get).mockResolvedValue({ data: emptyPage });
    const store = useCommentsStore();
    const draft = {
      username: "Alice1",
      email: "alice@example.com",
      homepage: "",
      text: "Reply",
      captcha_id: "captcha-id",
      captcha_answer: "ABC123",
    };

    const created = await store.create(draft, "parent-id");

    expect(created).toBe(true);
    expect(api.post).toHaveBeenCalledWith("/comments/parent-id/replies", draft);
    expect(api.get).toHaveBeenCalledOnce();
  });

  it("merges a live reply into its open branch without duplicates", () => {
    const store = useCommentsStore();
    const root: CommentItem = {
      id: "root-id",
      author_name: "Alice",
      author_email: "alice@example.com",
      homepage: "",
      html_text: "Root",
      text: "Root",
      parent_id: null,
      root_id: "root-id",
      depth: 0,
      score: 0,
      created_at: "2026-08-19T12:00:00Z",
      has_more_replies: false,
      avatar_url: null,
      attachments: [],
      replies: [],
    };
    const reply: CommentItem = {
      ...root,
      id: "reply-id",
      html_text: "Reply",
      text: "Reply",
      parent_id: root.id,
      depth: 1,
      replies: [],
    };
    store.comments = [root];

    store.mergeComment(reply);
    store.mergeComment(reply);

    expect(store.comments[0]?.replies).toEqual([reply]);
  });

  it("loads a branch before navigating to a search result", async () => {
    const root: CommentItem = {
      id: "root-id",
      author_name: "Alice",
      author_email: "alice@example.com",
      homepage: "",
      html_text: "Root",
      text: "Root",
      parent_id: null,
      root_id: "root-id",
      depth: 0,
      score: 0,
      created_at: "2026-08-19T12:00:00Z",
      has_more_replies: false,
      avatar_url: null,
      attachments: [],
      replies: [],
    };
    vi.mocked(api.get).mockResolvedValue({ data: root });
    const store = useCommentsStore();

    expect(await store.ensureLoaded("root-id")).toBe(true);

    expect(api.get).toHaveBeenCalledWith("/comments/root-id", { params: { depth: 10 } });
    expect(store.comments).toEqual([root]);
  });

  it("appends the next root page without duplicates", async () => {
    const root = {
      id: "root-id",
      author_name: "Alice",
      author_email: "alice@example.com",
      homepage: "",
      html_text: "Root",
      text: "Root",
      parent_id: null,
      root_id: "root-id",
      depth: 0,
      score: 0,
      created_at: "2026-08-19T12:00:00Z",
      has_more_replies: false,
      avatar_url: null,
      attachments: [],
      replies: [],
    } satisfies CommentItem;
    const nextRoot = { ...root, id: "next-root", root_id: "next-root" };
    vi.mocked(api.get).mockResolvedValue({
      data: { next: null, previous: "/comments", results: [root, nextRoot] },
    });
    const store = useCommentsStore();
    store.comments = [root];
    store.nextPage = "/comments?cursor=next";

    await store.loadMore();

    expect(api.get).toHaveBeenCalledWith("/comments?cursor=next");
    expect(store.comments.map((comment) => comment.id)).toEqual(["root-id", "next-root"]);
    expect(store.nextPage).toBeNull();
  });
});
