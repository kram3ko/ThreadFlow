<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue";

import { api } from "../api";
import { LatestRequest } from "../search/latestRequest";
import type { SearchResult } from "../types";

const MIN_CHARS = 2;
const DEBOUNCE_MS = 300;

const emit = defineEmits<{ select: [id: string] }>();
const query = ref("");
const results = ref<SearchResult[]>([]);
const source = ref("");
const loading = ref(false);
const searched = ref(false);
const lastQuery = ref("");
const error = ref("");
const requests = new LatestRequest();
let debounce: ReturnType<typeof setTimeout> | undefined;

watch(query, (value) => {
  clearTimeout(debounce);
  if (value.trim().length < MIN_CHARS) {
    requests.cancel();
    results.value = [];
    source.value = "";
    searched.value = false;
    loading.value = false;
    error.value = "";
    return;
  }
  debounce = setTimeout(() => void search(), DEBOUNCE_MS);
});

function highlightParts(text: string): { text: string; match: boolean }[] {
  if (!lastQuery.value) return [{ text, match: false }];
  const escaped = lastQuery.value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return text.split(new RegExp(`(${escaped})`, "gi")).filter(Boolean).map((part) => ({
    text: part,
    match: part.toLowerCase() === lastQuery.value.toLowerCase(),
  }));
}

async function search() {
  const searchQuery = query.value.trim();
  if (searchQuery.length < MIN_CHARS) return;
  const signal = requests.begin();
  loading.value = true;
  error.value = "";
  try {
    const { data } = await api.get<{ source: string; results: SearchResult[] }>("/search", {
      params: { q: searchQuery },
      signal,
    });
    if (!requests.isCurrent(signal)) return;
    lastQuery.value = searchQuery;
    source.value = data.source;
    results.value = data.results;
    searched.value = true;
  } catch {
    if (requests.isCurrent(signal)) error.value = "Search is temporarily unavailable.";
  } finally {
    if (requests.isCurrent(signal)) loading.value = false;
  }
}

onBeforeUnmount(() => {
  clearTimeout(debounce);
  requests.cancel();
});
</script>

<template>
  <section class="search-panel">
    <form class="search-form" @submit.prevent="search">
      <input v-model="query" type="search" placeholder="Search comments and authors…" />
      <button class="primary compact" type="submit" :disabled="loading">Search</button>
    </form>
    <small v-if="loading">Searching…</small>
    <small v-else-if="source">{{ results.length }} found · source: {{ source }}</small>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="searched && !loading && !results.length" class="empty">
      No matches for “{{ lastQuery }}”.
    </p>
    <ul v-if="results.length" class="search-results">
      <li v-for="result in results" :key="result.id">
        <button type="button" class="search-hit" @click="emit('select', result.id)">
          <strong>{{ result.author_name }}</strong> —
          <template v-for="(part, index) in highlightParts(result.highlights.join(' … '))" :key="index">
            <mark v-if="part.match">{{ part.text }}</mark><template v-else>{{ part.text }}</template>
          </template>
        </button>
      </li>
    </ul>
  </section>
</template>
