import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "../src/api";
import { useAuthStore } from "../src/stores/auth";
import type { AuthUser } from "../src/types";

vi.mock("../src/api", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const user: AuthUser = {
  id: "user-id",
  username: "Alice",
  email: "alice@example.com",
  created_at: "2026-08-19T12:00:00Z",
};

describe("auth store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("registers without exposing tokens to application state", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { csrf_token: "csrf" } });
    vi.mocked(api.post).mockResolvedValue({ data: user });
    const store = useAuthStore();

    const registered = await store.register({
      username: "Alice",
      email: "alice@example.com",
      password: "correct horse battery staple",
    });

    expect(registered).toBe(true);
    expect(store.user).toEqual(user);
    expect(api.post).toHaveBeenCalledWith("/auth/register", {
      username: "Alice",
      email: "alice@example.com",
      password: "correct horse battery staple",
    });
    expect(Object.keys(store.$state)).not.toContain("accessToken");
    expect(Object.keys(store.$state)).not.toContain("refreshToken");
  });

  it("restores a session with the refresh cookie", async () => {
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: { csrf_token: "csrf" } })
      .mockRejectedValueOnce({ isAxiosError: true, response: { status: 401 } });
    vi.mocked(api.post).mockResolvedValue({ data: user });
    const store = useAuthStore();

    await store.initialize();

    expect(api.post).toHaveBeenCalledWith("/auth/refresh");
    expect(store.user).toEqual(user);
    expect(store.initialized).toBe(true);
  });
});
