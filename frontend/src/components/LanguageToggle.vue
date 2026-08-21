<script setup lang="ts">
import { Locale, useI18n } from "../i18n";

const { locale, setLocale, t } = useI18n();
</script>

<template>
  <label class="language-toggle">
    <span class="visually-hidden">{{ t("language") }}</span>
    <select
      :value="locale"
      :aria-label="t('language')"
      @change="setLocale(($event.target as HTMLSelectElement).value as Locale)"
    >
      <option :value="Locale.English">EN</option>
      <option :value="Locale.Ukrainian">УКР</option>
      <option :value="Locale.Russian">RU</option>
    </select>
  </label>
</template>
