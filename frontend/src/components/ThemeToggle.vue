<script setup lang="ts">
import { ThemeMode, useTheme } from "../theme";
import { useI18n } from "../i18n";

const theme = useTheme();
const { t } = useI18n();
</script>

<template>
  <label class="theme-toggle">
    <span class="visually-hidden">{{ t("theme") }}</span>
    <select
      :value="theme.mode.value"
      :aria-label="t('theme')"
      @change="theme.setTheme(($event.target as HTMLSelectElement).value as ThemeMode)"
    >
      <option :value="ThemeMode.Auto">{{ t("auto") }}</option>
      <option :value="ThemeMode.Light">{{ t("light") }}</option>
      <option :value="ThemeMode.Dark">{{ t("dark") }}</option>
    </select>
  </label>
</template>
