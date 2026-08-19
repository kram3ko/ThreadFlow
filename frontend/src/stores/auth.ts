import axios from "axios";
import { defineStore } from "pinia";

import { api } from "../api";
import type { AuthUser, LoginDraft, RegisterDraft } from "../types";

function errorMessage(error: unknown, fallback: string): string {
  if (!axios.isAxiosError(error)) return fallback;
  const details = error.response?.data?.error?.details;
  if (typeof details === "string") return details;
  if (details && typeof details === "object") {
    return Object.values(details).flat().join(" ") || fallback;
  }
  return fallback;
}

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null as AuthUser | null,
    initialized: false,
    loading: false,
    error: "",
  }),
  actions: {
    async initialize() {
      if (this.initialized) return;
      await this.ensureCsrf();
      try {
        const { data } = await api.get<AuthUser>("/auth/me");
        this.user = data;
      } catch (error: unknown) {
        if (axios.isAxiosError(error) && error.response?.status === 401) {
          await this.restoreWithRefresh();
        }
      } finally {
        this.initialized = true;
      }
    },
    async ensureCsrf() {
      await api.get("/auth/csrf");
    },
    async restoreWithRefresh() {
      try {
        const { data } = await api.post<AuthUser>("/auth/refresh");
        this.user = data;
      } catch {
        this.user = null;
      }
    },
    async login(draft: LoginDraft) {
      return this.submitAuth("/auth/login", draft);
    },
    async register(draft: RegisterDraft) {
      return this.submitAuth("/auth/register", draft);
    },
    async submitAuth(endpoint: string, draft: LoginDraft | RegisterDraft) {
      this.loading = true;
      this.error = "";
      try {
        await this.ensureCsrf();
        const { data } = await api.post<AuthUser>(endpoint, draft);
        this.user = data;
        return true;
      } catch (error: unknown) {
        this.error = errorMessage(error, "Authentication failed");
        return false;
      } finally {
        this.loading = false;
      }
    },
    async logout() {
      this.loading = true;
      this.error = "";
      try {
        await api.post("/auth/logout");
        this.user = null;
      } catch (error: unknown) {
        this.error = errorMessage(error, "Unable to sign out");
      } finally {
        this.loading = false;
      }
    },
  },
});
