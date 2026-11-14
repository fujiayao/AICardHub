<script setup lang="ts">
import { computed } from 'vue'
import { useModelStore } from '@/stores/model'
const props = defineProps<{ model?: string }>()
const state = useModelStore()
state.ensure()
const demo = computed(() => state.mode === 'fake' || import.meta.env.VITE_LOCAL_DEMO === 'true' || /fake|demo|local|演示/i.test(props.model || ''))
</script>
<template><div v-if="demo" class="notice" role="note">本地演示模型 · 回答用于本地功能验证</div><p v-else-if="state.error" class="muted small">{{ state.error }}</p></template>
