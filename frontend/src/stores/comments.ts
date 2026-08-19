import axios from "axios";
import { defineStore } from "pinia";

import { api } from "../api";
import type { CommentDraft, CommentItem, CommentPage } from "../types";

export const useCommentsStore = defineStore("comments", {
  state: () => ({
    comments: [] as CommentItem[],
    loading: false,
    error: "",
  }),
  actions: {
    async load(sort = "date", direction = "desc") {
      this.loading = true;
      this.error = "";
      try {
        const { data } = await api.get<CommentPage>("/comments", {
          params: { sort, direction },
        });
        this.comments = data.results;
      } catch (error: unknown) {
        this.error = axios.isAxiosError(error) ? error.message : "Unable to load comments";
      } finally {
        this.loading = false;
      }
    },
    async create(draft: CommentDraft, parentId?: string) {
      this.error = "";
      try {
        const endpoint = parentId ? `/comments/${parentId}/replies` : "/comments";
        await api.post(endpoint, draft);
        await this.load();
        return true;
      } catch (error: unknown) {
        this.error = axios.isAxiosError(error) ? error.message : "Unable to create comment";
        return false;
      }
    },
  },
});
