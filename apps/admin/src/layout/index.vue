<script setup lang="ts">
// Adapted from pure-admin-thin f0ff132 layout: responsive sidebar, header, breadcrumb and content.
import { shallowRef, watch } from "vue";
import { useRoute } from "vue-router";
import NavVertical from "./components/lay-sidebar/NavVertical.vue";
import LayContent from "./components/lay-content/index.vue";
import LayTag from "./components/lay-tag/index.vue";
import AppIcon from "@/components/shared/AppIcon.vue";
import { useBoolean } from "./hooks/useBoolean";
import { useAuthStore } from "@/store/modules/auth";
const { bool: collapsed, toggle } = useBoolean(false);
const auth = useAuthStore();
const route = useRoute();
const mobileOpen = shallowRef(false);
watch(
  () => route.path,
  () => (mobileOpen.value = false),
);
</script>
<template>
  <div :class="['app-wrapper', { collapsed }]">
    <a class="skip-link" href="#main-content">跳到主要内容</a>
    <aside class="sidebar" aria-label="侧边栏">
      <div class="brand">
        <span class="mark" aria-hidden="true">AI</span>
        <span v-if="!collapsed" class="brand-text"
          ><strong>数科 AI 智能名片</strong><small>管理后台</small></span
        >
      </div>
      <NavVertical :collapse="collapsed" />
    </aside>
    <div class="main-container">
      <header class="navbar">
        <button
          type="button"
          class="icon-btn desktop-toggle"
          :aria-label="collapsed ? '展开侧边栏' : '收起侧边栏'"
          :aria-expanded="!collapsed"
          @click="toggle"
        >
          <AppIcon name="collapse" />
        </button>
        <button
          type="button"
          class="icon-btn mobile-toggle"
          aria-label="打开管理菜单"
          :aria-expanded="mobileOpen"
          @click="mobileOpen = true"
        >
          <AppIcon name="menu" />
        </button>
        <LayTag />
        <div class="account">
          <span class="avatar" aria-hidden="true">{{
            auth.session?.staff.name?.slice(0, 1) ?? "管"
          }}</span>
          <span class="account-name">{{ auth.session?.staff.name }}</span>
          <span class="role">管理员</span>
        </div>
        <button
          type="button"
          class="icon-btn"
          aria-label="退出登录"
          title="退出登录"
          @click="auth.logout"
        >
          <AppIcon name="logout" />
        </button>
      </header>
      <LayContent />
    </div>
    <el-drawer
      v-model="mobileOpen"
      title="管理菜单"
      direction="ltr"
      size="min(280px,85vw)"
      class="nav-drawer"
      ><NavVertical :collapse="false" @select="mobileOpen = false"
    /></el-drawer>
  </div>
</template>
<style scoped>
.app-wrapper {
  display: flex;
  min-height: 100vh;
  background: var(--ac-bg);
}
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  width: var(--ac-sidebar-w);
  flex-shrink: 0;
  background: var(--ac-navy);
  color: var(--ac-on-navy);
  transition: width 200ms ease;
}
.collapsed .sidebar {
  width: var(--ac-sidebar-w-collapsed);
}
.brand {
  height: var(--ac-header-h);
  display: flex;
  align-items: center;
  gap: var(--ac-space-3);
  padding: 0 var(--ac-space-4);
  border-bottom: 1px solid var(--ac-navy-2);
  white-space: nowrap;
}
.mark {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border-radius: var(--ac-radius-sm);
  background: var(--ac-teal);
  font-size: 13px;
  font-weight: 700;
}
.brand-text {
  display: grid;
  line-height: 1.25;
}
.brand-text strong {
  font-size: 14px;
}
.brand-text small {
  font-size: 12px;
  color: var(--ac-on-navy-muted);
}
.main-container {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
}
.navbar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  gap: var(--ac-space-3);
  align-items: center;
  height: var(--ac-header-h);
  padding: 0 var(--ac-space-5);
  background: var(--ac-surface);
  border-bottom: 1px solid var(--ac-border);
}
.icon-btn {
  display: inline-grid;
  place-items: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border: 1px solid transparent;
  border-radius: var(--ac-radius-sm);
  background: transparent;
  color: var(--ac-text-muted);
  cursor: pointer;
}
.icon-btn:hover {
  background: var(--ac-surface-muted);
  border-color: var(--ac-border);
  color: var(--ac-text);
}
.account {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: var(--ac-space-2);
  min-width: 0;
}
.avatar {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--ac-primary-soft);
  color: var(--ac-primary);
  font-size: 13px;
  font-weight: 650;
}
.account-name {
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.role {
  font-size: 12px;
  padding: 1px 8px;
  border-radius: 999px;
  background: var(--ac-teal-soft);
  color: var(--ac-teal);
}
.mobile-toggle {
  display: none;
}
@media (max-width: 760px) {
  .sidebar,
  .desktop-toggle,
  .role {
    display: none;
  }
  .mobile-toggle {
    display: inline-grid;
  }
  .navbar {
    padding: 0 var(--ac-space-3);
    gap: var(--ac-space-2);
  }
}
</style>
<style>
.nav-drawer.el-drawer {
  background: var(--ac-navy);
}
.nav-drawer .el-drawer__header {
  color: var(--ac-on-navy);
  border-bottom-color: var(--ac-navy-2);
}
.nav-drawer .el-drawer__body {
  padding: 0;
}
</style>
