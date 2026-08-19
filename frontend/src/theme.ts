import { ref } from "vue";

export enum ThemeMode {
  Auto = "auto",
  Light = "light",
  Dark = "dark",
}

const STORAGE_KEY = "threadflow.theme";
const mode = ref<ThemeMode>(ThemeMode.Auto);
const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");

function resolvedTheme(): ThemeMode.Light | ThemeMode.Dark {
  if (mode.value !== ThemeMode.Auto) return mode.value;
  return systemTheme.matches ? ThemeMode.Dark : ThemeMode.Light;
}

function applyTheme(): void {
  document.documentElement.dataset.theme = resolvedTheme();
  document.documentElement.style.colorScheme = resolvedTheme();
}

export function initializeTheme(): void {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (Object.values(ThemeMode).includes(saved as ThemeMode)) mode.value = saved as ThemeMode;
  applyTheme();
}

export function useTheme() {
  function setTheme(nextMode: ThemeMode): void {
    mode.value = nextMode;
    localStorage.setItem(STORAGE_KEY, nextMode);
    applyTheme();
  }

  return { mode, setTheme };
}

systemTheme.addEventListener("change", () => {
  if (mode.value === ThemeMode.Auto) applyTheme();
});
