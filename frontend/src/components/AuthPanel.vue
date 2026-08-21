<script setup lang="ts">
import { reactive, ref, useTemplateRef } from "vue";

import { useAuthStore } from "../stores/auth";
import { api } from "../api";
import { useI18n } from "../i18n";

const auth = useAuthStore();
const mode = ref<"login" | "register">("login");
const draft = reactive({ username: "", email: "", password: "" });
const dialog = useTemplateRef<HTMLDialogElement>("auth-dialog");
const { t } = useI18n();

function open(nextMode: "login" | "register") {
  mode.value = nextMode;
  auth.error = "";
  dialog.value?.showModal();
}

function close() {
  dialog.value?.close();
}

async function submit() {
  const success =
    mode.value === "login"
      ? await auth.login({ username: draft.username, password: draft.password })
      : await auth.register({ ...draft });
  if (success) {
    draft.password = "";
    dialog.value?.close();
  }
}

async function uploadAvatar(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  const form = new FormData();
  form.append("file", file);
  form.append("purpose", "avatar");
  await api.post("/attachments", form);
  const { data } = await api.get("/auth/me");
  auth.user = data;
}
</script>

<template>
  <div v-if="auth.user" class="account-actions auth-session">
    <label class="avatar-picker" :title="t('changeAvatar')">
      <img v-if="auth.user.avatar_url" class="avatar avatar-image" :src="auth.user.avatar_url" alt="" />
      <span v-else class="avatar" aria-hidden="true">{{ auth.user.username.charAt(0).toUpperCase() }}</span>
      <input type="file" accept="image/jpeg,image/png,image/gif" @change="uploadAvatar" />
    </label>
    <strong>{{ auth.user.username }}</strong>
    <button class="link-button" type="button" :disabled="auth.loading" @click="auth.logout">
      {{ t("signOut") }}
    </button>
  </div>

  <div v-else class="account-actions">
    <button class="link-button" type="button" @click="open('login')">{{ t("signIn") }}</button>
    <button class="primary compact" type="button" @click="open('register')">{{ t("register") }}</button>
  </div>

  <dialog ref="auth-dialog" class="auth-dialog">
    <div class="dialog-heading">
      <h2>{{ mode === "login" ? t("welcomeBack") : t("createAccount") }}</h2>
      <button class="dialog-close" type="button" :aria-label="t('close')" @click="close">×</button>
    </div>
    <div class="auth-tabs">
      <button
        type="button"
        :class="{ active: mode === 'login' }"
        @click="mode = 'login'"
      >
        {{ t("signIn") }}
      </button>
      <button
        type="button"
        :class="{ active: mode === 'register' }"
        @click="mode = 'register'"
      >
        {{ t("register") }}
      </button>
    </div>
    <form class="auth-form modal-form" @submit.prevent="submit">
      <label>
        {{ mode === "login" ? t("usernameOrEmail") : t("username") }}
        <input v-model="draft.username" required autocomplete="username" />
      </label>
      <label v-if="mode === 'register'">
        {{ t("email") }} <input v-model="draft.email" required type="email" autocomplete="email" />
      </label>
      <label>
        {{ t("password") }}
        <input
          v-model="draft.password"
          required
          minlength="8"
          type="password"
          :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
        />
      </label>
      <button class="primary" type="submit" :disabled="auth.loading">
        {{ auth.loading ? t("pleaseWait") : mode === "login" ? t("signIn") : t("createAccount") }}
      </button>
    </form>
    <p v-if="auth.error" class="error">{{ auth.error }}</p>
  </dialog>
</template>
