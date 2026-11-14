<script setup lang="ts">
defineProps<{ loading?: boolean, error?: string, empty?: boolean, emptyText?: string }>()
defineEmits<{ retry: [] }>()
</script>
<template>
 <div v-if="loading" class="state panel" role="status" aria-label="正在加载"><van-skeleton title avatar :row="4" /></div>
 <div v-else-if="error" class="state panel state-error" role="alert">
  <span class="icon i-lucide-cloud-off" aria-hidden="true" />
  <h2>加载没有成功</h2>
  <p class="muted">{{ error }}</p>
  <van-button plain type="primary" @click="$emit('retry')">重新加载</van-button>
 </div>
 <div v-else-if="empty" class="state state-empty">
  <span class="icon i-lucide-inbox" aria-hidden="true" />
  <p class="muted">{{ emptyText || '暂时没有内容' }}</p>
  <slot name="empty-action" />
 </div>
 <slot v-else />
</template>
<style scoped>
.state{margin:var(--sp-4)}
.state-error,.state-empty{display:grid;justify-items:center;gap:var(--sp-3);text-align:center;padding:var(--sp-8) var(--sp-5)}
.state-error .icon,.state-empty .icon{width:40px;height:40px;color:var(--c-text-3)}
.state-error .van-button{min-width:140px;min-height:44px}
</style>
