<script setup lang="ts">
// Breadcrumb derived from route meta (replaces upstream tag chrome).
import { computed } from "vue";
import { useRoute } from "vue-router";
const route = useRoute();
const group = computed(() => route.meta.group ?? "管理后台");
</script>
<template>
  <nav class="crumbs" aria-label="当前位置">
    <ol>
      <li class="crumb-group">{{ group }}</li>
      <li aria-current="page" class="current">{{ route.meta.title }}</li>
    </ol>
  </nav>
</template>
<style scoped>
.crumbs {
  min-width: 0;
}
ol {
  display: flex;
  align-items: center;
  gap: var(--ac-space-2);
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: 14px;
  white-space: nowrap;
}
li + li::before {
  content: "/";
  margin-right: var(--ac-space-2);
  color: var(--ac-border-strong);
}
.crumb-group {
  color: var(--ac-text-subtle);
}
.current {
  color: var(--ac-text);
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
}
@media (max-width: 760px) {
  .crumb-group {
    display: none;
  }
  li + li::before {
    content: none;
  }
}
</style>
