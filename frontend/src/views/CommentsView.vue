<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

import AuthPanel from "../components/AuthPanel.vue";
import CommentForm from "../components/CommentForm.vue";
import CommentNode from "../components/CommentNode.vue";
import ThemeToggle from "../components/ThemeToggle.vue";
import LanguageToggle from "../components/LanguageToggle.vue";
import SearchPanel from "../components/SearchPanel.vue";
import { useI18n } from "../i18n";
import { useCommentsStore } from "../stores/comments";
import { useAuthStore } from "../stores/auth";
import type { CommentItem } from "../types";

const store = useCommentsStore();
const auth = useAuthStore();
const sort = ref("date");
const direction = ref("desc");
const replyTo = ref<CommentItem | null>(null);
const highlightedId = ref<string | null>(null);
const composerOpen = ref(false);
const HIGHLIGHT_MS = 2000;
const { t } = useI18n();

function socketLabel() {
  if (store.socketStatus === "open") return t("live");
  if (store.socketStatus === "connecting") return t("connecting");
  return t("closed");
}

function reload() {
  return store.load(sort.value, direction.value);
}

function selectReply(comment: CommentItem) {
  replyTo.value = replyTo.value?.id === comment.id ? null : comment;
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
      <div class="brand">
        <span class="brand-mark" aria-hidden="true">TF</span>
        <div class="hero">
          <h1>ThreadFlow</h1>
          <p>{{ t("tagline") }}</p>
        </div>
      </div>
      <div class="topbar-actions">
        <LanguageToggle />
        <ThemeToggle />
        <AuthPanel />
      </div>
    </header>

    <section class="composer-shell" :class="{ expanded: composerOpen }">
      <button v-if="!composerOpen" class="composer-invite" type="button" @click="composerOpen = true">
        <span class="composer-plus" aria-hidden="true">+</span>
        <span><strong>{{ t("joinDiscussion") }}</strong><small>{{ t("joinHint") }}</small></span>
        <span class="composer-arrow" aria-hidden="true">→</span>
      </button>
      <CommentForm
        v-else
        :submit="store.create"
        :parent="null"
        :user="auth.user"
        closable
        @cancel="composerOpen = false"
        @submitted="composerOpen = false"
      />
    </section>

    <SearchPanel @select="selectComment" />

    <section class="feed">
      <div class="feed-toolbar">
        <h2>{{ t("comments") }}</h2>
        <span class="connection-state" :class="store.socketStatus">
          {{ socketLabel() }}
        </span>
        <div class="sort-controls">
          <select v-model="sort" :aria-label="t('sortField')" @change="reload">
            <option value="date">{{ t("date") }}</option>
            <option value="name">{{ t("name") }}</option>
            <option value="email">{{ t("email") }}</option>
          </select>
          <select v-model="direction" :aria-label="t('sortDirection')" @change="reload">
            <option value="desc">{{ t("descending") }}</option>
            <option value="asc">{{ t("ascending") }}</option>
          </select>
        </div>
      </div>

      <p v-if="store.error" class="error">{{ store.error }}</p>
      <button v-if="store.pendingRoots" class="new-comments" type="button" @click="reload">
        {{ t("newComments", { count: store.pendingRoots }) }}
      </button>
      <div v-if="store.loading" class="skeleton-list" :aria-label="t('loading')">
        <span v-for="index in 3" :key="index" class="comment-skeleton" />
      </div>
      <div v-else-if="!store.comments.length" class="empty-state">
        <span aria-hidden="true">✦</span>
        <p>{{ t("emptyThread") }}</p>
      </div>
      <template v-else>
        <CommentNode
          v-for="comment in store.comments"
          :key="comment.id"
          :comment="comment"
          :highlighted-id="highlightedId"
          :reply-to-id="replyTo?.id ?? null"
          @reply="selectReply"
          @reply-closed="replyTo = null"
        />
        <button
          v-if="store.nextPage"
          class="load-more"
          type="button"
          :disabled="store.loadingMore"
          @click="store.loadMore"
        >{{ store.loadingMore ? t("loading") : t("loadMoreComments") }}</button>
      </template>
    </section>
  </main>
</template>
