<script setup lang="ts">
import { useRouter } from 'vue-router'
const props = defineProps<{ title: string, back?: boolean }>()
const router = useRouter()
function goBack() { if (window.history.length > 1) router.back(); else router.push('/staff/card') }
</script>
<template><main class="page"><van-nav-bar :title="props.title" :left-arrow="back" :left-text="back ? '返回' : undefined" @click-left="goBack"><template #title><h1 class="nav-title">{{ props.title }}</h1></template><template #right><slot name="action" /></template></van-nav-bar><div class="content"><slot /></div><slot name="footer" /></main></template>

<style scoped>.nav-title{font-size:var(--fs-md);font-weight:600}</style>
