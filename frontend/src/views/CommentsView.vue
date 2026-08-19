<script setup lang="ts">
import { onMounted, ref, watch } from "vue";

import AuthPanel from "../components/AuthPanel.vue";
import CommentForm from "../components/CommentForm.vue";
import CommentNode from "../components/CommentNode.vue";
import ThemeToggle from "../components/ThemeToggle.vue";
import SearchPanel from "../components/SearchPanel.vue";
import { useCommentsStore } from "../stores/comments";
import { useAuthStore } from "../stores/auth";
import type { CommentItem } from "../types";

const store = useCommentsStore();
const auth = useAuthStore();
const sort = ref("date");
const direction = ref("desc");
const replyTo = ref<CommentItem | null>(null);

function reload() {
  return store.load(sort.value, direction.value);
}

onMounted(() => {
  void auth.initialize();
  void reload();
  store.startRealtime();
});

watch(
  () => auth.user?.id,
  (current, previous) => {
    if (current !== previous && auth.initialized) store.reconnectRealtime();
  },
);
</script>

<template>
  <main class="page-shell">
    <header class="topbar">
      <div class="hero">
        <span class="eyebrow">Threaded conversations</span>
        <h1>ThreadFlow</h1>
        <p>Focused discussions that keep their context.</p>
      </div>
      <div class="topbar-actions">
        <ThemeToggle />
        <AuthPanel />
      </div>
    </header>

    <CommentForm
      :submit="store.create"
      :parent="replyTo"
      :user="auth.user"
      @submitted="replyTo = null"
      @cancel="replyTo = null"
    />

    <SearchPanel />

    <section class="feed">
      <div class="feed-toolbar">
        <h2>Comments</h2>
        <span class="connection-state" :class="store.socketStatus">
          {{ store.socketStatus === "open" ? "Live" : store.socketStatus }}
        </span>
        <div class="sort-controls">
          <select v-model="sort" aria-label="Sort field" @change="reload">
            <option value="date">Date</option>
            <option value="name">Name</option>
            <option value="email">Email</option>
          </select>
          <select v-model="direction" aria-label="Sort direction" @change="reload">
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </div>
      </div>

      <p v-if="store.error" class="error">{{ store.error }}</p>
      <button v-if="store.pendingRoots" class="new-comments" type="button" @click="reload">
        {{ store.pendingRoots }} new comments
      </button>
      <p v-if="store.loading">Loading…</p>
      <p v-else-if="!store.comments.length" class="empty">No comments yet. Start the thread.</p>
      <template v-else>
        <CommentNode
          v-for="comment in store.comments"
          :key="comment.id"
          :comment="comment"
          @reply="replyTo = $event"
        />
      </template>
    </section>
  </main>
</template>
