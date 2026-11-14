import { defineStore } from "pinia";
import { shallowRef, computed } from "vue";
import { api } from "@/api/adapters";
import {
  readSession,
  clearSession,
  tokenExpired,
  SESSION_KEY,
} from "@/api/session";
import type { Login } from "@/api/schema";
export const useAuthStore = defineStore("aicardhub-admin", () => {
  const session = shallowRef<Login | null>(readSession());
  const authenticated = computed(
    () => !!session.value && !tokenExpired(session.value.token),
  );
  function persist(value: Login) {
    session.value = value;
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(value));
  }
  async function login(phone: string, password: string) {
    const result = await api.login({ phone, password });
    if (result.staff.role !== "admin") {
      logout();
      throw new Error("此入口仅允许管理员登录");
    }
    persist(result);
  }
  function logout() {
    session.value = null;
    clearSession();
  }
  function changedPassword() {
    if (session.value) persist({ ...session.value, must_change_pwd: false });
  }
  function requirePassword() {
    if (session.value) persist({ ...session.value, must_change_pwd: true });
  }
  window.addEventListener("admin-session-ended", () => {
    session.value = null;
  });
  return {
    session,
    authenticated,
    login,
    logout,
    changedPassword,
    requirePassword,
  };
});
