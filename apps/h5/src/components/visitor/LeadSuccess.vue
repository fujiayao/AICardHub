<script setup lang="ts">
import { callPhone } from '@/platform'
import { maskPhone } from '@/utils/format'
defineProps<{ name: string, phone?: string | null, summary: { name: string, phone: string, company_name: string }, code: string }>()
defineEmits<{ continue: [] }>()
</script>
<template><main class="content result"><span class="icon i-lucide-circle-check result-icon" aria-hidden="true" /><h1>已提交</h1><p>{{ name }}会尽快与您联系</p><section class="panel stack"><p>{{ summary.name }}</p><p class="num">{{ maskPhone(summary.phone) }}</p><p v-if="summary.company_name">{{ summary.company_name }}</p></section><van-button block type="primary" @click="$emit('continue')">继续聊聊</van-button><van-button block :to="`/card/${code}`">返回名片</van-button><button v-if="phone" class="text-button" @click="callPhone(phone)">直接拨打 {{ phone }}</button></main></template>
<style scoped>.result{padding-top:96px;text-align:center}.result-icon{width:64px;height:64px;color:var(--c-success);margin:auto}</style>
