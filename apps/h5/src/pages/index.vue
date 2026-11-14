<!-- 原型: B1 入口 -->
<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
const router = useRouter()
onMounted(() => router.replace('/staff/card'))
</script>
<template><div role="status">正在打开数科名片…</div></template>
