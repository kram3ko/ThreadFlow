<script setup lang="ts">
import { nextTick, onMounted, reactive, ref, useTemplateRef } from "vue";

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
const attachment = ref<File | null>(null);
const fileInput = useTemplateRef<HTMLInputElement>("fileInput");
const commentInput = useTemplateRef<HTMLTextAreaElement>("commentInput");
const uploadError = ref("");
const previewing = ref(false);
const previewHtml = ref("");
const previewError = ref("");
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
  } catch {
    captcha.value = null;
  } finally {
    captchaLoading.value = false;
  }
}

function clearAttachment() {
  attachment.value = null;
  if (fileInput.value) fileInput.value.value = "";
}

function wrap(tag: string, attributes = "") {
  const el = commentInput.value;
  if (!el) return;
  const start = el.selectionStart;
  const end = el.selectionEnd;
  const open = attributes ? `<${tag} ${attributes}>` : `<${tag}>`;
  const close = `</${tag}>`;
  draft.text = draft.text.slice(0, start) + open + draft.text.slice(start, end) + close + draft.text.slice(end);
  void nextTick(() => {
    el.focus();
    const caret = start + open.length;
    el.setSelectionRange(caret, caret + (end - start));
  });
}

function insertLink() {
  const url = window.prompt("Link URL", "https://");
  if (!url) return;
  wrap("a", `href="${url.replaceAll('"', "%22")}"`);
}

async function togglePreview() {
  if (previewing.value) {
    previewing.value = false;
    return;
  }
  previewError.value = "";
  try {
    const { data } = await api.post<{ html: string }>("/comments/preview", { text: draft.text });
    previewHtml.value = data.html;
  } catch {
    previewHtml.value = "";
    previewError.value = "Preview failed — check that your tags are closed.";
  }
  previewing.value = true;
}

async function uploadAttachment(file: File): Promise<{ id: string; token: string } | null> {
  const form = new FormData();
  form.append("file", file);
  form.append("purpose", "comment");
  try {
    const { data } = await api.post<{ id: string; claim_token: string }>("/attachments", form);
    return { id: data.id, token: data.claim_token };
  } catch {
    uploadError.value = "Unable to upload the attachment.";
    return null;
  }
}

async function submit() {
  submitting.value = true;
  uploadError.value = "";
  try {
    const payload: CommentDraft = { ...draft };
    if (attachment.value) {
      const claim = await uploadAttachment(attachment.value);
      if (!claim) return;
      payload.attachments = [claim];
    }
    const success = await props.submit(payload, props.parent?.id);
    await loadCaptcha();
    if (success) {
      draft.text = "";
      previewing.value = false;
      previewHtml.value = "";
      clearAttachment();
      emit("submitted");
    }
  } finally {
    submitting.value = false;
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
    <p v-if="uploadError" class="error">{{ uploadError }}</p>
    <div class="form-grid">
      <p v-if="user" class="posting-as">Posting as <strong>{{ user.username }}</strong></p>
      <template v-else>
        <label>Username <input v-model="draft.username" required pattern="[A-Za-z0-9_]+" /></label>
        <label>Email <input v-model="draft.email" required type="email" /></label>
      </template>
      <label class="wide">Homepage <input v-model="draft.homepage" type="url" /></label>
      <div class="wide comment-editor">
        <span class="editor-label">Comment</span>
        <div class="editor-toolbar" role="group" aria-label="Formatting">
          <button type="button" title="Bold" @click="wrap('strong')"><strong>B</strong></button>
          <button type="button" title="Italic" @click="wrap('i')"><em>i</em></button>
          <button type="button" title="Code" @click="wrap('code')">&lt;/&gt;</button>
          <button type="button" title="Link" @click="insertLink">link</button>
          <button type="button" class="preview-btn" @click="togglePreview">
            {{ previewing ? "Hide preview" : "Preview" }}
          </button>
        </div>
        <textarea ref="commentInput" v-model="draft.text" required rows="5" />
        <div v-if="previewing" class="comment-preview">
          <p v-if="previewError" class="error">{{ previewError }}</p>
          <div v-else class="comment-text" v-html="previewHtml" />
        </div>
      </div>
      <label class="wide">
        Attachment (JPG, PNG, GIF or TXT)
        <span class="attachment-control">
          <input
            ref="fileInput"
            type="file"
            accept="image/jpeg,image/png,image/gif,text/plain,.txt"
            @change="attachment = ($event.target as HTMLInputElement).files?.[0] ?? null"
          />
          <button
            v-if="attachment"
            type="button"
            class="attachment-remove"
            aria-label="Remove attachment"
            @click="clearAttachment"
          >×</button>
        </span>
      </label>
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
