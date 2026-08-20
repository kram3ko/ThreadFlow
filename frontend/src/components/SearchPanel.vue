<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from "vue";

import { api } from "../api";
import { LatestRequest } from "../search/latestRequest";
import type { SearchResult } from "../types";
import { useI18n } from "../i18n";

const MIN_CHARS = 2;
const DEBOUNCE_MS = 300;
const PAGE_SIZE = 20;

interface SearchParams {
  q: string;
  author: string;
  date_from?: string;
  date_to?: string;
  sort: "relevance" | "date";
  direction: "asc" | "desc";
  limit: number;
  offset: number;
}

interface SearchResponse {
  source: string;
  results: SearchResult[];
  next_offset: number | null;
}

const emit = defineEmits<{ select: [id: string] }>();
const { formatDate, t } = useI18n();
const query = ref("");
const results = ref<SearchResult[]>([]);
const source = ref("");
const loading = ref(false);
const searched = ref(false);
const lastQuery = ref("");
const error = ref("");
const nextOffset = ref<number | null>(null);
const lastParams = ref<SearchParams | null>(null);
const filters = reactive({
  author: "",
  dateFrom: "",
  dateTo: "",
  sort: "relevance" as "relevance" | "date",
  direction: "desc" as "asc" | "desc",
});
const activeFilterCount = computed(
  () => [filters.author, filters.dateFrom, filters.dateTo].filter(Boolean).length
    + (filters.sort !== "relevance" ? 1 : 0)
    + (filters.direction !== "desc" ? 1 : 0),
);
const requests = new LatestRequest();
let debounce: ReturnType<typeof setTimeout> | undefined;

watch(query, (value) => {
  clearTimeout(debounce);
  const length = value.trim().length;
  if (length === 1) {
    requests.cancel();
    loading.value = false;
    return;
  }
  if (length === 0 && activeFilterCount.value === 0) {
    clearSearch();
    return;
  }
  debounce = setTimeout(() => void search(), DEBOUNCE_MS);
});

function clearSearch() {
  requests.cancel();
  results.value = [];
  source.value = "";
  searched.value = false;
  loading.value = false;
  error.value = "";
  nextOffset.value = null;
  lastParams.value = null;
}

function boundary(date: string, endOfDay = false): string | undefined {
  if (!date) return undefined;
  return `${date}T${endOfDay ? "23:59:59.999" : "00:00:00"}Z`;
}

function currentParams(): SearchParams {
  return {
    q: query.value.trim(),
    author: filters.author.trim(),
    date_from: boundary(filters.dateFrom),
    date_to: boundary(filters.dateTo, true),
    sort: filters.sort,
    direction: filters.direction,
    limit: PAGE_SIZE,
    offset: 0,
  };
}

function hasCriteria(params: SearchParams): boolean {
  return params.q.length >= MIN_CHARS || Boolean(params.author || params.date_from || params.date_to);
}

function highlightParts(text: string): { text: string; match: boolean }[] {
  if (!lastQuery.value) return [{ text, match: false }];
  const escaped = lastQuery.value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return text.split(new RegExp(`(${escaped})`, "gi")).filter(Boolean).map((part) => ({
    text: part,
    match: part.toLowerCase() === lastQuery.value.toLowerCase(),
  }));
}

async function search(append = false) {
  if (append && (nextOffset.value === null || !lastParams.value)) return;
  const params = append
    ? { ...lastParams.value!, offset: nextOffset.value! }
    : currentParams();
  if (!hasCriteria(params)) {
    error.value = t("searchCriteriaError");
    return;
  }
  const signal = requests.begin();
  loading.value = true;
  error.value = "";
  try {
    const { data } = await api.get<SearchResponse>("/search", {
      params,
      signal,
    });
    if (!requests.isCurrent(signal)) return;
    if (append) {
      const known = new Set(results.value.map((result) => result.id));
      results.value.push(...data.results.filter((result) => !known.has(result.id)));
    } else {
      results.value = data.results;
      lastParams.value = params;
      lastQuery.value = params.q;
    }
    source.value = data.source;
    nextOffset.value = data.next_offset;
    searched.value = true;
  } catch {
    if (requests.isCurrent(signal)) error.value = t("searchUnavailable");
  } finally {
    if (requests.isCurrent(signal)) loading.value = false;
  }
}

function resetFilters() {
  filters.author = "";
  filters.dateFrom = "";
  filters.dateTo = "";
  filters.sort = "relevance";
  filters.direction = "desc";
  if (query.value.trim().length >= MIN_CHARS) void search();
  else clearSearch();
}

onBeforeUnmount(() => {
  clearTimeout(debounce);
  requests.cancel();
});
</script>

<template>
  <section class="search-panel">
    <form class="search-controls" @submit.prevent="search()">
      <div class="search-form">
        <input
          v-model="query"
          :aria-label="t('searchQuery')"
          type="search"
          :placeholder="t('searchPlaceholder')"
        />
        <button class="primary compact" type="submit" :disabled="loading">{{ t("search") }}</button>
      </div>
      <details class="search-filters">
        <summary>
          {{ t("filters") }}
          <span v-if="activeFilterCount" class="filter-count">{{ activeFilterCount }}</span>
        </summary>
        <div class="filter-grid">
          <label>
            {{ t("author") }}
            <input v-model="filters.author" :placeholder="t('nameOrEmail')" />
          </label>
          <label>
            {{ t("fromDate") }}
            <input v-model="filters.dateFrom" type="date" :max="filters.dateTo || undefined" />
          </label>
          <label>
            {{ t("toDate") }}
            <input v-model="filters.dateTo" type="date" :min="filters.dateFrom || undefined" />
          </label>
          <label>
            {{ t("sortBy") }}
            <select v-model="filters.sort">
              <option value="relevance">{{ t("relevance") }}</option>
              <option value="date">{{ t("date") }}</option>
            </select>
          </label>
          <label>
            {{ t("direction") }}
            <select v-model="filters.direction">
              <option value="desc">{{ t("descending") }}</option>
              <option value="asc">{{ t("ascending") }}</option>
            </select>
          </label>
          <div class="filter-actions">
            <button class="primary compact" type="submit" :disabled="loading">{{ t("applyFilters") }}</button>
            <button class="link-button" type="button" @click="resetFilters">{{ t("reset") }}</button>
          </div>
        </div>
      </details>
    </form>
    <small v-if="loading">{{ t("searching") }}</small>
    <small v-else-if="source">
      {{ t("resultsLoaded", { count: results.length }) }}<span v-if="nextOffset !== null"> · {{ t("moreAvailable") }}</span>
      · {{ t("source") }}: {{ source }}
    </small>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="searched && !loading && !results.length" class="empty">
      {{ lastQuery ? t("noQueryMatches", { query: lastQuery }) : t("noFilterMatches") }}
    </p>
    <ul v-if="results.length" class="search-results">
      <li v-for="result in results" :key="result.id">
        <button type="button" class="search-hit" @click="emit('select', result.id)">
          <strong>{{ result.author_name }}</strong> —
          <template v-for="(part, index) in highlightParts(result.highlights.join(' … '))" :key="index">
            <mark v-if="part.match">{{ part.text }}</mark><template v-else>{{ part.text }}</template>
          </template>
          <time :datetime="result.created_at">{{ formatDate(result.created_at, true) }}</time>
        </button>
      </li>
    </ul>
    <button
      v-if="nextOffset !== null"
      class="load-more search-load-more"
      type="button"
      :disabled="loading"
      @click="search(true)"
    >{{ loading ? t("loading") : t("loadMoreResults") }}</button>
  </section>
</template>
