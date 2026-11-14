<script setup lang="ts">
// Adapted from pure-admin-thin f0ff132 layout: responsive sidebar, header, tags and content.
import { shallowRef } from "vue";
import NavVertical from "./components/lay-sidebar/NavVertical.vue";
import LayContent from "./components/lay-content/index.vue";
import LayTag from "./components/lay-tag/index.vue";
import { useBoolean } from "./hooks/useBoolean";
import { useAuthStore } from "@/store/modules/auth";
const { bool: collapsed, toggle } = useBoolean(false);
const auth = useAuthStore();
const mobileOpen = shallowRef(false);
</script>
<template>
  <div class="app-wrapper">
    <aside :class="['sidebar-container', { collapsed }]">
      <div class="brand">{{ collapsed ? "数科" : "数科 · 名片管理" }}</div>
      <NavVertical :collapse="collapsed" />
    </aside>
    <div class="main-container">
      <header class="navbar">
        <el-button class="desktop-toggle" @click="toggle">{{
          collapsed ? "展开菜单" : "收起菜单"
        }}</el-button
        ><el-button
          class="mobile-toggle"
          aria-label="打开管理菜单"
          @click="mobileOpen = true"
          >菜单</el-button
        ><span class="muted">本地候选</span
        ><span class="account">{{ auth.session?.staff.name }}</span
        ><el-button @click="auth.logout">退出登录</el-button>
      </header>
      <LayTag /><LayContent />
    </div>
    <el-drawer
      v-model="mobileOpen"
      title="管理菜单"
      direction="ltr"
      size="min(280px,85vw)"
      ><NavVertical :collapse="false" @select="mobileOpen = false"
    /></el-drawer>
  </div>
</template>
<style scoped>
.app-wrapper {
  display: flex;
  min-height: 100vh;
}
.sidebar-container {
  width: 216px;
  flex-shrink: 0;
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-light);
}
.sidebar-container.collapsed {
  width: 64px;
}
.brand {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  font-weight: 650;
  white-space: nowrap;
}
.main-container {
  min-width: 0;
  flex: 1;
}
.navbar {
  display: flex;
  gap: 16px;
  align-items: center;
  min-height: 64px;
  padding: 12px 24px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
}
.account {
  margin-left: auto;
}
.mobile-toggle {
  display: none;
}
@media (max-width: 760px) {
  .desktop-toggle {
    display: none;
  }
  .mobile-toggle {
    display: inline-flex;
    margin-left: 0;
  }
  .sidebar-container {
    display: none;
  }
  .brand {
    font-size: 12px;
    padding: 8px;
    white-space: normal;
  }
  .navbar {
    padding: 12px;
    gap: 8px;
    flex-wrap: wrap;
  }
  .navbar .muted {
    display: none;
  }
}
</style>
