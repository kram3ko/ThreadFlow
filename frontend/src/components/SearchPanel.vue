<script setup lang="ts">
import { ref } from "vue";

import { api } from "../api";
import type { SearchResult } from "../types";

const query = ref("");
const results = ref<SearchResult[]>([]);
const source = ref("");
const loading = ref(false);

function highlightParts(text: string): { text: string; match: boolean }[] {
  if (!query.value.trim()) return [{ text, match: false }];
  const escaped = query.value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return text.split(new RegExp(`(${escaped})`, "gi")).filter(Boolean).map((part) => ({
    text: part,
    match: part.toLowerCase() === query.value.toLowerCase(),
  }));
}

async function search() {
  loading.value = true;
  try {
    const { data } = await api.get<{ source: string; results: SearchResult[] }>("/search", {
      params: { q: query.value },
    });
    source.value = data.source;
    results.value = data.results;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="search-panel">
    <form class="search-form" @submit.prevent="search">
      <input v-model="query" type="search" placeholder="Search comments and authors" />
      <button class="primary compact" type="submit" :disabled="loading">Search</button>
    </form>
    <small v-if="source">Source: {{ source }}</small>
    <ul v-if="results.length" class="search-results">
      <li v-for="result in results" :key="result.id">
        <strong>{{ result.author_name }}</strong> —
        <template v-for="(part, index) in highlightParts(result.highlights.join(' … '))" :key="index">
          <mark v-if="part.match">{{ part.text }}</mark><template v-else>{{ part.text }}</template>
        </template>
      </li>
    </ul>
  </section>
</template>
