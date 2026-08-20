<script setup lang="ts">
import { ref, useTemplateRef } from "vue";

import type { AttachmentItem, CommentItem } from "../types";
import { avatarInitial, avatarStyle } from "../avatar";
import { useCommentsStore } from "../stores/comments";

defineOptions({ name: "CommentNode" });
const props = defineProps<{ comment: CommentItem; highlightedId: string | null }>();
const emit = defineEmits<{ reply: [comment: CommentItem] }>();
const store = useCommentsStore();
const lightbox = useTemplateRef<HTMLDialogElement>("lightbox");
const selectedImage = ref<{ url: string; name: string } | null>(null);
const selectedText = ref<{ content: string; name: string } | null>(null);
const previewLoading = ref(false);
const previewError = ref("");

function voteKey(id: string): string {
  return `vote:${id}`;
}
const myVote = ref(Number(localStorage.getItem(voteKey(props.comment.id)) ?? 0));
const copied = ref(false);

async function copyLink() {
  const url = `${location.origin}${location.pathname}#comment-${props.comment.id}`;
  try {
    await navigator.clipboard.writeText(url);
    copied.value = true;
    setTimeout(() => (copied.value = false), 1200);
  } catch {
    copied.value = false;
  }
}

function openImage(url: string, name: string) {
  selectedImage.value = { url, name };
  selectedText.value = null;
  previewError.value = "";
  lightbox.value?.showModal();
}

async function openAttachment(attachment: AttachmentItem) {
  if (attachment.kind === "image") {
    openImage(attachment.content_url, attachment.original_name);
    return;
  }
  selectedImage.value = null;
  selectedText.value = null;
  previewError.value = "";
  previewLoading.value = true;
  lightbox.value?.showModal();
  try {
    const response = await fetch(attachment.content_url, { credentials: "same-origin" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    selectedText.value = {
      content: await response.text(),
      name: attachment.original_name,
    };
  } catch {
    previewError.value = "Unable to load text preview";
  } finally {
    previewLoading.value = false;
  }
}

async function cast(value: 1 | -1) {
  const next = (myVote.value === value ? 0 : value) as -1 | 0 | 1;
  if (!(await store.vote(props.comment.id, next))) return;
  myVote.value = next;
  if (next === 0) localStorage.removeItem(voteKey(props.comment.id));
  else localStorage.setItem(voteKey(props.comment.id), String(next));
}
</script>

<template>
  <article :id="`comment-${comment.id}`" class="comment" :class="{ flash: comment.id === highlightedId }">
    <header>
      <img v-if="comment.avatar_url" class="avatar avatar-image" :src="comment.avatar_url" alt="" />
      <span v-else class="avatar" :style="avatarStyle(comment.author_name)" aria-hidden="true">
        {{ avatarInitial(comment.author_name) }}
      </span>
      <span class="comment-meta">
        <strong>{{ comment.author_name }}</strong>
        <time :datetime="comment.created_at">{{ new Date(comment.created_at).toLocaleString() }}</time>
      </span>
      <div class="comment-actions">
        <button
          type="button"
          class="action-icon"
          :title="copied ? 'Link copied' : 'Copy link'"
          aria-label="Copy link to comment"
          @click="copyLink"
        >{{ copied ? "✓" : "#" }}</button>
        <button
          type="button"
          class="action-icon"
          title="Reply"
          aria-label="Reply"
          @click="emit('reply', comment)"
        >↩</button>
        <span class="votes">
          <button
            type="button"
            class="vote"
            :class="{ active: myVote === 1 }"
            aria-label="Upvote"
            @click="cast(1)"
          >▲</button>
          <span class="score" :class="{ positive: comment.score > 0, negative: comment.score < 0 }">
            {{ comment.score }}
          </span>
          <button
            type="button"
            class="vote"
            :class="{ active: myVote === -1 }"
            aria-label="Downvote"
            @click="cast(-1)"
          >▼</button>
        </span>
      </div>
    </header>
    <div class="comment-text" v-html="comment.html_text" />
    <div v-if="comment.attachments.length" class="attachments">
      <button
        v-for="item in comment.attachments"
        :key="item.id"
        class="attachment"
        type="button"
        @click="openAttachment(item)"
      >
        <img v-if="item.kind === 'image'" :src="item.content_url" :alt="item.original_name" />
        <span v-else>📄 {{ item.original_name }} · {{ Math.ceil(item.size / 1024) }} KB</span>
      </button>
    </div>
    <dialog ref="lightbox" class="lightbox" @click.self="lightbox?.close()">
      <button class="dialog-close" type="button" aria-label="Close" @click="lightbox?.close()">×</button>
      <img v-if="selectedImage" :src="selectedImage.url" :alt="selectedImage.name" />
      <p v-else-if="previewLoading" class="text-preview-state">Loading preview…</p>
      <p v-else-if="previewError" class="error">{{ previewError }}</p>
      <section v-else-if="selectedText" class="text-preview">
        <h3>{{ selectedText.name }}</h3>
        <pre>{{ selectedText.content }}</pre>
      </section>
    </dialog>
    <div v-if="comment.replies.length" class="replies">
      <CommentNode
        v-for="reply in comment.replies"
        :key="reply.id"
        :comment="reply"
        :highlighted-id="highlightedId"
        @reply="emit('reply', $event)"
      />
    </div>
    <button
      v-if="comment.has_more_replies"
      class="more-replies"
      type="button"
      @click="store.loadBranch(comment.id)"
    >Load more replies</button>
  </article>
</template>
