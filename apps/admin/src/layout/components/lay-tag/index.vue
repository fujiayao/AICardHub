<script setup lang="ts">
import { useRoute } from "vue-router";
import TagChrome from "./components/TagChrome.vue";
const route = useRoute();
</script>
<template>
  <nav class="tags" aria-label="当前位置">
    <span>管理后台 /</span
    ><span class="tag"
      ><TagChrome class="shape" /><span class="title">{{
        route.meta.title
      }}</span></span
    >
  </nav>
</template>
<style scoped>
.tags {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 24px;
  border-bottom: 1px solid var(--el-border-color-light);
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.tag {
  position: relative;
  padding: 8px 20px;
  color: var(--el-color-primary);
  min-width: 100px;
  text-align: center;
}
.shape {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0.08;
}
.title {
  position: relative;
}
</style>
