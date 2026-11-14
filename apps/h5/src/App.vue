<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>
<template><RouterView v-slot="{ Component, route }"><component :is="Component" :key="`${route.path}:${route.query.e || 'business'}:${route.query.s || 'link'}`" /></RouterView></template>
