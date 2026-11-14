<script setup lang="ts">
defineProps<{ title: string; reason: string; steps?: string[] }>();
</script>
<template>
  <section class="panel" role="status">
    <div class="pending-state">
      <span class="tag">待后端契约</span>
      <strong>{{ title }}</strong>
      <span>{{ reason }}</span>
    </div>
    <div v-if="steps?.length" class="plan">
      <h2>契约就绪后将提供</h2>
      <ol>
        <li v-for="s in steps" :key="s">{{ s }}</li>
      </ol>
    </div>
  </section>
</template>
<style scoped>
.tag {
  justify-self: start;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--ac-warning-soft);
  color: var(--ac-warning);
}
.plan {
  margin-top: var(--ac-space-5);
}
.plan ol {
  margin: var(--ac-space-3) 0 0;
  padding-left: var(--ac-space-5);
  color: var(--ac-text-muted);
  font-size: 14px;
  line-height: 1.9;
}
</style>
