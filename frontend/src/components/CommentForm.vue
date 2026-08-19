<script setup lang="ts">
import { reactive, ref } from "vue";

import type { AuthUser, CommentDraft, CommentItem } from "../types";

const props = defineProps<{
  parent: CommentItem | null;
  user: AuthUser | null;
  submit: (draft: CommentDraft, parentId?: string) => Promise<boolean>;
}>();
const emit = defineEmits<{ submitted: []; cancel: [] }>();
const submitting = ref(false);
const draft = reactive<CommentDraft>({ username: "", email: "", homepage: "", text: "" });

async function submit() {
  submitting.value = true;
  const success = await props.submit({ ...draft }, props.parent?.id);
  submitting.value = false;
  if (success) {
    draft.text = "";
    emit("submitted");
  }
}

</script>

<template>
  <form class="comment-form" @submit.prevent="submit">
    <div class="form-heading">
      <h2>{{ parent ? `Reply to ${parent.author_name}` : "Add comment" }}</h2>
      <button v-if="parent" class="link-button" type="button" @click="emit('cancel')">Cancel</button>
    </div>
    <div class="form-grid">
      <p v-if="user" class="posting-as">Posting as <strong>{{ user.username }}</strong></p>
      <template v-else>
        <label>Username <input v-model="draft.username" required pattern="[A-Za-z0-9_]+" /></label>
        <label>Email <input v-model="draft.email" required type="email" /></label>
      </template>
      <label class="wide">Homepage <input v-model="draft.homepage" type="url" /></label>
      <label class="wide">Comment <textarea v-model="draft.text" required rows="5" /></label>
    </div>
    <button class="primary" type="submit" :disabled="submitting">
      {{ submitting ? "Sending…" : "Send comment" }}
    </button>
  </form>
</template>
