<script setup lang="ts">
// Upstream lay-content reduced to the project's single static router outlet.
</script>
<template>
  <main id="main-content" class="app-main" tabindex="-1">
    <router-view v-slot="{ Component, route }"
      ><component :is="Component" :key="route.path"
    /></router-view>
  </main>
</template>
<style scoped>
.app-main {
  flex: 1;
  width: 100%;
  max-width: 1440px;
  margin: 0 auto;
  padding: var(--ac-space-5);
  min-width: 0;
}
.app-main:focus {
  outline: none;
}
@media (max-width: 760px) {
  .app-main {
    padding: var(--ac-space-3);
  }
}
</style>
