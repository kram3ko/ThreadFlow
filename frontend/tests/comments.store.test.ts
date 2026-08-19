import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "../src/api";
import { useCommentsStore } from "../src/stores/comments";
import type { CommentPage } from "../src/types";

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
});
