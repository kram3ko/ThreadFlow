<script setup lang="ts">
import { nextTick, onMounted, reactive, ref, useTemplateRef } from "vue";

import { api } from "../api";
import { useI18n } from "../i18n";
import type { AuthUser, CaptchaChallenge, CommentDraft, CommentItem } from "../types";

const props = defineProps<{
  parent: CommentItem | null;
  user: AuthUser | null;
  submit: (draft: CommentDraft, parentId?: string) => Promise<boolean>;
  closable?: boolean;
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
const { t } = useI18n();
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
  const url = window.prompt(t("linkUrl"), "https://");
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
    previewError.value = t("previewFailed");
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
    uploadError.value = t("uploadFailed");
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
    if (success) {
      draft.text = "";
      previewing.value = false;
      previewHtml.value = "";
      clearAttachment();
      emit("submitted");
      if (!props.parent && !props.closable) await loadCaptcha();
    } else {
      await loadCaptcha();
    }
  } finally {
    submitting.value = false;
  }
}

onMounted(() => {
  void loadCaptcha();
  if (props.parent) void nextTick(() => commentInput.value?.focus());
});

</script>

<template>
  <form class="comment-form" @submit.prevent="submit">
    <div class="form-heading">
      <div>
        <span v-if="parent" class="form-context">{{ t("reply") }}</span>
        <h2>{{ parent ? t("replyTo", { name: parent.author_name }) : t("addComment") }}</h2>
      </div>
      <button v-if="parent || closable" class="link-button" type="button" @click="emit('cancel')">{{ t("cancel") }}</button>
    </div>
    <p v-if="uploadError" class="error">{{ uploadError }}</p>
    <div class="form-grid">
      <p v-if="user" class="posting-as">{{ t("postingAs") }} <strong>{{ user.username }}</strong></p>
      <template v-else>
        <label>{{ t("username") }} <input v-model="draft.username" required pattern="[A-Za-z0-9_]+" /></label>
        <label>{{ t("email") }} <input v-model="draft.email" required type="email" /></label>
      </template>
      <label class="wide">{{ t("homepage") }} <input v-model="draft.homepage" type="url" /></label>
      <div class="wide comment-editor">
        <div class="editor-tabs">
          <button type="button" :class="{ active: !previewing }" @click="previewing = false">{{ t("write") }}</button>
          <button type="button" :class="{ active: previewing }" @click="togglePreview">{{ t("preview") }}</button>
        </div>
        <div v-show="!previewing" class="editor-surface">
          <div class="editor-toolbar" role="group" :aria-label="t('formatting')">
            <button type="button" :title="t('bold')" @click="wrap('strong')"><strong>B</strong></button>
            <button type="button" :title="t('italic')" @click="wrap('i')"><em>i</em></button>
            <button type="button" :title="t('code')" @click="wrap('code')">&lt;/&gt;</button>
            <button type="button" :title="t('link')" @click="insertLink">↗</button>
          </div>
          <textarea ref="commentInput" v-model="draft.text" required rows="5" :placeholder="t('commentPlaceholder')" />
          <small class="character-count">{{ t("characters", { count: draft.text.length }) }}</small>
        </div>
        <div v-if="previewing" class="comment-preview">
          <p v-if="previewError" class="error">{{ previewError }}</p>
          <div v-else-if="previewHtml" class="comment-text" v-html="previewHtml" />
          <p v-else class="preview-placeholder">{{ t("commentPlaceholder") }}</p>
        </div>
      </div>
      <label class="wide attachment-field">
        <span>{{ t("attachment") }} <small>· {{ t("attachmentHint") }}</small></span>
        <span class="attachment-control">
          <input
            ref="fileInput"
            type="file"
            accept="image/jpeg,image/png,image/gif,text/plain,.txt"
            @change="attachment = ($event.target as HTMLInputElement).files?.[0] ?? null"
          />
          <span class="file-trigger">＋ {{ t("chooseFile") }}</span>
          <span v-if="attachment" class="file-chip">{{ attachment.name }}</span>
          <button
            v-if="attachment"
            type="button"
            class="attachment-remove"
            :aria-label="t('removeAttachment')"
            @click="clearAttachment"
          >×</button>
        </span>
      </label>
      <div class="captcha-field wide">
        <img v-if="captcha" :src="captcha.image_data" :alt="t('captchaAlt')" width="190" height="64" />
        <span v-else>{{ captchaLoading ? t("captchaLoading") : t("captchaUnavailable") }}</span>
        <label>
          {{ t("captcha") }}
          <input
            v-model="draft.captcha_answer"
            required
            :disabled="captchaLoading || !captcha"
            autocomplete="off"
            pattern="[A-Za-z0-9]+"
          />
        </label>
        <button class="link-button" type="button" :disabled="captchaLoading" @click="loadCaptcha">
          {{ t("newImage") }}
        </button>
      </div>
    </div>
    <button class="primary" type="submit" :disabled="submitting || captchaLoading || !captcha">
      {{ submitting ? t("sending") : t("sendComment") }}
    </button>
  </form>
</template>
