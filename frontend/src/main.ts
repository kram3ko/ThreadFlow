import { createPinia } from "pinia";
import { createApp } from "vue";

import App from "./App.vue";
import router from "./router";
import "./styles.css";
import { initializeI18n } from "./i18n";
import { initializeTheme } from "./theme";

initializeI18n();
initializeTheme();
createApp(App).use(createPinia()).use(router).mount("#app");
