<script setup lang="ts">
import { reactive, ref, useTemplateRef } from "vue";

import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const mode = ref<"login" | "register">("login");
const draft = reactive({ username: "", email: "", password: "" });
const dialog = useTemplateRef<HTMLDialogElement>("auth-dialog");

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
</script>

<template>
  <div v-if="auth.user" class="account-actions auth-session">
    <span class="avatar" aria-hidden="true">{{ auth.user.username.charAt(0).toUpperCase() }}</span>
    <strong>{{ auth.user.username }}</strong>
    <button class="link-button" type="button" :disabled="auth.loading" @click="auth.logout">
      Sign out
    </button>
  </div>

  <div v-else class="account-actions">
    <button class="link-button" type="button" @click="open('login')">Sign in</button>
    <button class="primary compact" type="button" @click="open('register')">Register</button>
  </div>

  <dialog ref="auth-dialog" class="auth-dialog">
    <div class="dialog-heading">
      <h2>{{ mode === "login" ? "Welcome back" : "Create account" }}</h2>
      <button class="dialog-close" type="button" aria-label="Close" @click="close">×</button>
    </div>
    <div class="auth-tabs">
      <button
        type="button"
        :class="{ active: mode === 'login' }"
        @click="mode = 'login'"
      >
        Sign in
      </button>
      <button
        type="button"
        :class="{ active: mode === 'register' }"
        @click="mode = 'register'"
      >
        Register
      </button>
    </div>
    <form class="auth-form modal-form" @submit.prevent="submit">
      <label>Username <input v-model="draft.username" required autocomplete="username" /></label>
      <label v-if="mode === 'register'">
        Email <input v-model="draft.email" required type="email" autocomplete="email" />
      </label>
      <label>
        Password
        <input
          v-model="draft.password"
          required
          minlength="8"
          type="password"
          :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
        />
      </label>
      <button class="primary" type="submit" :disabled="auth.loading">
        {{ auth.loading ? "Please wait…" : mode === "login" ? "Sign in" : "Create account" }}
      </button>
    </form>
    <p v-if="auth.error" class="error">{{ auth.error }}</p>
  </dialog>
</template>
