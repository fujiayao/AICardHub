import { createRouter, createWebHistory } from "vue-router";
import { adminRoutes } from "./modules/admin";
import { installAuthNavigation } from "./guard";
import { useAuthStore } from "@/store/modules/auth";
import { tokenExpired } from "@/api/session";
import { store } from "@/store";
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: "/login", component: () => import("@/views/Login.vue") },
    {
      path: "/change-password",
      component: () => import("@/views/ChangePassword.vue"),
    },
    // Backward-compatible alias for old links; keeps query and hash.
    {
      path: "/activity",
      redirect: (to) => ({
        path: "/activities",
        query: to.query,
        hash: to.hash,
      }),
    },
    {
      path: "/",
      component: () => import("@/layout/index.vue"),
      redirect: "/dashboard",
      children: adminRoutes,
    },
    { path: "/:pathMatch(.*)*", redirect: "/dashboard" },
  ],
});
router.beforeEach((to) => {
  document.title = `${to.meta.title ?? "管理员登录"} · 数科名片管理后台`;
});
installAuthNavigation(router, {
  auth: () => {
    const auth = useAuthStore(store);
    const signedIn =
      auth.authenticated && !(auth.session && tokenExpired(auth.session.token));
    return { signedIn, mustChangePassword: !!auth.session?.must_change_pwd };
  },
  requirePassword: () => useAuthStore(store).requirePassword(),
  events: window,
});
window.setInterval(() => {
  const auth = useAuthStore(store);
  if (auth.session && tokenExpired(auth.session.token)) auth.logout();
}, 10000);
export default router;
