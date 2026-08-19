<script setup lang="ts">
import type { CommentItem } from "../types";
import { avatarInitial, avatarStyle } from "../avatar";

defineOptions({ name: "CommentNode" });
defineProps<{ comment: CommentItem }>();
const emit = defineEmits<{ reply: [comment: CommentItem] }>();
</script>

<template>
  <article class="comment">
    <header>
      <span class="avatar" :style="avatarStyle(comment.author_name)" aria-hidden="true">
        {{ avatarInitial(comment.author_name) }}
      </span>
      <span class="comment-meta">
        <strong>{{ comment.author_name }}</strong>
        <time :datetime="comment.created_at">{{ new Date(comment.created_at).toLocaleString() }}</time>
      </span>
    </header>
    <div class="comment-text" v-html="comment.html_text" />
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
