import { createRouter, createWebHistory } from "vue-router";

import CommentsView from "./views/CommentsView.vue";

export default createRouter({
  history: createWebHistory(),
  routes: [{ path: "/", component: CommentsView }],
});
