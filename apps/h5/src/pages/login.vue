<!-- 原型: B1 登录快捷入口 -->
<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
const route = useRoute(); const router = useRouter()
onMounted(() => router.replace({ path: '/staff/login', query: route.query }))
</script>
<template><div role="status">正在打开员工登录…</div></template>
