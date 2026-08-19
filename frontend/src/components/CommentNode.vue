<script setup lang="ts">
import type { CommentItem } from "../types";

defineOptions({ name: "CommentNode" });
defineProps<{ comment: CommentItem }>();
const emit = defineEmits<{ reply: [comment: CommentItem] }>();
</script>

<template>
  <article class="comment">
    <header>
      <strong>{{ comment.author_name }}</strong>
      <time :datetime="comment.created_at">{{ new Date(comment.created_at).toLocaleString() }}</time>
    </header>
    <p class="comment-text">{{ comment.text }}</p>
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
