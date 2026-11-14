import { createRouter, createWebHistory } from "vue-router";
import { adminRoutes } from "./modules/admin";
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
  const auth = useAuthStore(store);
  document.title = `${to.meta.title ?? "管理员登录"} · 数科名片管理后台`;
  if (
    (!auth.authenticated ||
      (auth.session && tokenExpired(auth.session.token))) &&
    to.path !== "/login"
  )
    return "/login";
  if (
    auth.authenticated &&
    auth.session?.must_change_pwd &&
    to.path !== "/change-password"
  )
    return "/change-password";
  if (auth.authenticated && to.path === "/login") return "/dashboard";
});
window.addEventListener("admin-session-ended", () => {
  void router.replace("/login");
});
window.addEventListener("admin-password-required", () => {
  useAuthStore(store).requirePassword();
  void router.replace("/change-password");
});
window.setInterval(() => {
  const auth = useAuthStore(store);
  if (auth.session && tokenExpired(auth.session.token)) auth.logout();
}, 10000);
export default router;
