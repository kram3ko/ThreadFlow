import axios from "axios";
import { defineStore } from "pinia";

import { api } from "../api";
import { CommentOperation, type SocketStatus } from "../realtime/contracts";
import { CommentsSocket, SocketCommandError } from "../realtime/commentsSocket";
import type { CommentDraft, CommentItem, CommentPage } from "../types";

function findComment(comments: CommentItem[], id: string): CommentItem | null {
  for (const comment of comments) {
    if (comment.id === id) return comment;
    const nested = findComment(comment.replies, id);
    if (nested) return nested;
  }
  return null;
}

function socketErrorMessage(error: SocketCommandError): string {
  if (typeof error.details === "string") return error.details;
  if (error.details && typeof error.details === "object") {
    return Object.values(error.details).flat().join(" ") || "Unable to create comment";
  }
  return "Unable to create comment";
}

export const useCommentsStore = defineStore("comments", {
  state: () => ({
    comments: [] as CommentItem[],
    loading: false,
    error: "",
    sort: "date",
    direction: "desc",
    socketStatus: "closed" as SocketStatus,
    pendingRoots: 0,
    socket: null as CommentsSocket | null,
  }),
  actions: {
    async load(sort = "date", direction = "desc") {
      this.sort = sort;
      this.direction = direction;
      this.loading = true;
      this.error = "";
      try {
        const { data } = await api.get<CommentPage>("/comments", {
          params: { sort, direction },
        });
        this.comments = data.results;
        this.pendingRoots = 0;
      } catch (error: unknown) {
        this.error = axios.isAxiosError(error) ? error.message : "Unable to load comments";
      } finally {
        this.loading = false;
      }
    },
    async create(draft: CommentDraft, parentId?: string) {
      this.error = "";
      if (this.socket?.isOpen) {
        const operation = parentId ? CommentOperation.Reply : CommentOperation.Create;
        const data = parentId ? { ...draft, parent_id: parentId } : draft;
        try {
          const response = await this.socket.request(operation, data);
          this.mergeComment(response.data.comment);
          return true;
        } catch (error: unknown) {
          this.error =
            error instanceof SocketCommandError
              ? socketErrorMessage(error)
              : "Unable to create comment";
          return false;
        }
      }
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
    startRealtime() {
      if (this.socket) return;
      let openedBefore = false;
      this.socket = new CommentsSocket(
        (comment) => this.mergeComment(comment),
        (status) => {
          const reconnect = status === "open" && openedBefore;
          this.socketStatus = status;
          if (status === "open") openedBefore = true;
          if (reconnect) void this.load(this.sort, this.direction);
        },
      );
      this.socket.connect();
    },
    reconnectRealtime() {
      this.socket?.reconnect();
    },
    mergeComment(comment: CommentItem) {
      if (findComment(this.comments, comment.id)) return;
      if (comment.parent_id) {
        const parent = findComment(this.comments, comment.parent_id);
        if (parent) parent.replies.push(comment);
        return;
      }
      if (this.sort === "date" && this.direction === "desc") {
        this.comments.unshift(comment);
      } else {
        this.pendingRoots += 1;
      }
    },
  },
});
