<script setup lang="ts">
import { ThemeMode, useTheme } from "../theme";

const theme = useTheme();
</script>

<template>
  <label class="theme-toggle">
    <span>Theme</span>
    <select
      :value="theme.mode.value"
      aria-label="Color theme"
      @change="theme.setTheme(($event.target as HTMLSelectElement).value as ThemeMode)"
    >
      <option :value="ThemeMode.Auto">Auto</option>
      <option :value="ThemeMode.Light">Light</option>
      <option :value="ThemeMode.Dark">Dark</option>
    </select>
  </label>
</template>
