<script setup lang="ts">
import { ref, useTemplateRef } from "vue";

import type { CommentItem } from "../types";
import { avatarInitial, avatarStyle } from "../avatar";

defineOptions({ name: "CommentNode" });
defineProps<{ comment: CommentItem }>();
const emit = defineEmits<{ reply: [comment: CommentItem] }>();
const lightbox = useTemplateRef<HTMLDialogElement>("lightbox");
const selectedImage = ref<{ url: string; name: string } | null>(null);

function openImage(url: string, name: string) {
  selectedImage.value = { url, name };
  lightbox.value?.showModal();
}
</script>

<template>
  <article class="comment">
    <header>
      <img v-if="comment.avatar_url" class="avatar avatar-image" :src="comment.avatar_url" alt="" />
      <span v-else class="avatar" :style="avatarStyle(comment.author_name)" aria-hidden="true">
        {{ avatarInitial(comment.author_name) }}
      </span>
      <span class="comment-meta">
        <strong>{{ comment.author_name }}</strong>
        <time :datetime="comment.created_at">{{ new Date(comment.created_at).toLocaleString() }}</time>
      </span>
    </header>
    <div class="comment-text" v-html="comment.html_text" />
    <div v-if="comment.attachments.length" class="attachments">
      <button
        v-for="item in comment.attachments"
        :key="item.id"
        class="attachment"
        type="button"
        @click="item.kind === 'image' && openImage(item.content_url, item.original_name)"
      >
        <img v-if="item.kind === 'image'" :src="item.content_url" :alt="item.original_name" />
        <a
          v-else
          :href="item.content_url"
          target="_blank"
          rel="noopener noreferrer"
          @click.stop
        >📄 {{ item.original_name }} · {{ Math.ceil(item.size / 1024) }} KB</a>
      </button>
    </div>
    <dialog ref="lightbox" class="lightbox" @click.self="lightbox?.close()">
      <button class="dialog-close" type="button" aria-label="Close" @click="lightbox?.close()">×</button>
      <img v-if="selectedImage" :src="selectedImage.url" :alt="selectedImage.name" />
    </dialog>
    <button class="link-button" type="button" @click="emit('reply', comment)">Reply</button>
    <div v-if="comment.replies.length" class="replies">
      <CommentNode
        v-for="reply in comment.replies"
        :key="reply.id"
        :comment="reply"
        @reply="emit('reply', $event)"
      />
    </div>
    <p v-else-if="comment.has_more_replies" class="more-replies">More replies are available.</p>
  </article>
</template>
