<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import { api } from "../api";
import type { AuthUser, CaptchaChallenge, CommentDraft, CommentItem } from "../types";

const props = defineProps<{
  parent: CommentItem | null;
  user: AuthUser | null;
  submit: (draft: CommentDraft, parentId?: string) => Promise<boolean>;
}>();
const emit = defineEmits<{ submitted: []; cancel: [] }>();
const submitting = ref(false);
const captcha = ref<CaptchaChallenge | null>(null);
const captchaLoading = ref(false);
const draft = reactive<CommentDraft>({
  username: "",
  email: "",
  homepage: "",
  text: "",
  captcha_id: "",
  captcha_answer: "",
});

async function loadCaptcha() {
  captchaLoading.value = true;
  try {
    const { data } = await api.get<CaptchaChallenge>("/captcha");
    captcha.value = data;
    draft.captcha_id = data.id;
    draft.captcha_answer = "";
  } finally {
    captchaLoading.value = false;
  }
}

async function submit() {
  submitting.value = true;
  const success = await props.submit({ ...draft }, props.parent?.id);
  submitting.value = false;
  await loadCaptcha();
  if (success) {
    draft.text = "";
    emit("submitted");
  }
}

onMounted(() => void loadCaptcha());

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
      <div class="captcha-field wide">
        <img v-if="captcha" :src="captcha.image_data" alt="CAPTCHA challenge" width="190" height="64" />
        <span v-else>{{ captchaLoading ? "Loading CAPTCHA…" : "CAPTCHA unavailable" }}</span>
        <label>
          CAPTCHA
          <input
            v-model="draft.captcha_answer"
            required
            autocomplete="off"
            pattern="[A-Za-z0-9]+"
          />
        </label>
        <button class="link-button" type="button" :disabled="captchaLoading" @click="loadCaptcha">
          New image
        </button>
      </div>
    </div>
    <button class="primary" type="submit" :disabled="submitting">
      {{ submitting ? "Sending…" : "Send comment" }}
    </button>
  </form>
</template>
