<script setup lang="ts">
import { reactive, ref } from "vue";

import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const mode = ref<"login" | "register">("login");
const draft = reactive({ username: "", email: "", password: "" });

async function submit() {
  const success =
    mode.value === "login"
      ? await auth.login({ username: draft.username, password: draft.password })
      : await auth.register({ ...draft });
  if (success) draft.password = "";
}
</script>

<template>
  <section v-if="auth.user" class="auth-panel auth-session">
    <div>
      <span class="eyebrow">Signed in</span>
      <strong>{{ auth.user.username }}</strong>
      <small>{{ auth.user.email }}</small>
    </div>
    <button class="link-button" type="button" :disabled="auth.loading" @click="auth.logout">
      Sign out
    </button>
  </section>

  <section v-else class="auth-panel">
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
    <form class="auth-form" @submit.prevent="submit">
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
  </section>
</template>
