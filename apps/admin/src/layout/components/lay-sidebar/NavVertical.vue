<script setup lang="ts">
// Adapted from upstream NavVertical: static menu data replaces permission/dynamic route stores.
import { useRoute } from "vue-router";
import { adminRoutes } from "@/router/modules/admin";
defineProps<{ collapse: boolean }>();
const route = useRoute();
</script>
<template>
  <el-menu
    router
    :default-active="route.path"
    :collapse="collapse"
    :collapse-transition="false"
    :class="['menu', { compact: collapse }]"
    ><el-menu-item
      v-for="item in adminRoutes"
      :key="item.path"
      :index="item.path"
      ><span class="compact-label">{{
        String(item.meta?.title).slice(0, 2)
      }}</span
      ><template #title>{{ item.meta?.title }}</template></el-menu-item
    ></el-menu
  >
</template>
<style scoped>
.menu {
  border: 0;
}
.compact-label {
  display: none;
}
.compact .compact-label {
  display: block;
}
@media (max-width: 760px) {
  .menu {
    width: 64px;
  }
  .menu :deep(.el-menu-item) {
    padding: 0 10px !important;
  }
  .menu :deep(.el-menu-item span:not(.compact-label)) {
    display: none;
  }
  .compact-label {
    display: block !important;
  }
}
</style>
