<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

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
const highlightedId = ref<string | null>(null);
const HIGHLIGHT_MS = 2000;

function reload() {
  return store.load(sort.value, direction.value);
}

function focusComment(id: string) {
  highlightedId.value = id;
  void nextTick(() => {
    document.getElementById(`comment-${id}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
  });
  window.setTimeout(() => {
    if (highlightedId.value === id) highlightedId.value = null;
  }, HIGHLIGHT_MS);
}

async function selectComment(id: string) {
  if (!(await store.ensureLoaded(id))) return;
  if (location.hash !== `#comment-${id}`) history.replaceState(null, "", `#comment-${id}`);
  focusComment(id);
}

async function focusFromHash() {
  const match = location.hash.match(/^#comment-([0-9a-f-]+)$/i);
  if (!match?.[1]) return;
  await selectComment(match[1]);
}

onMounted(async () => {
  void auth.initialize();
  await reload();
  store.startRealtime();
  void focusFromHash();
  window.addEventListener("hashchange", focusFromHash);
});

onBeforeUnmount(() => window.removeEventListener("hashchange", focusFromHash));

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

    <SearchPanel @select="selectComment" />

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
          :highlighted-id="highlightedId"
          @reply="replyTo = $event"
        />
        <button
          v-if="store.nextPage"
          class="load-more"
          type="button"
          :disabled="store.loadingMore"
          @click="store.loadMore"
        >{{ store.loadingMore ? "Loading…" : "Load 25 more comments" }}</button>
      </template>
    </section>
  </main>
</template>
