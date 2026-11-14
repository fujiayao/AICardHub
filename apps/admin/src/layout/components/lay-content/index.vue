<script setup lang="ts">
// Upstream lay-content reduced to the project's single static router outlet.
</script>
<template>
  <main class="app-main">
    <router-view v-slot="{ Component, route }"
      ><component :is="Component" :key="route.path"
    /></router-view>
  </main>
</template>
<style scoped>
.app-main {
  padding: 24px;
  min-width: 0;
}
@media (max-width: 760px) {
  .app-main {
    padding: 16px;
  }
}
</style>
