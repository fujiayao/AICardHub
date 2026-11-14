<script setup lang="ts">
import { callPhone } from '@/platform'
import { maskPhone } from '@/utils/format'
defineProps<{ name: string, phone?: string | null, summary: { name: string, phone: string, company_name: string }, code: string }>()
defineEmits<{ continue: [] }>()
</script>
<template><main class="content result"><span class="icon i-lucide-circle-check result-icon" aria-hidden="true" /><h1>已提交</h1><p class="lead-sub">{{ name }}会尽快与您联系</p><section class="panel summary"><p class="summary-name">{{ summary.name }}</p><p class="num phone">{{ maskPhone(summary.phone) }}</p><p v-if="summary.company_name" class="muted company">{{ summary.company_name }}</p></section><div class="actions"><van-button block type="primary" @click="$emit('continue')">继续聊聊</van-button><van-button block :to="`/card/${code}`">返回名片</van-button><button v-if="phone" class="text-button" @click="callPhone(phone)">直接拨打 {{ phone }}</button></div></main></template>
<style scoped>.result{padding-top:88px;text-align:center;display:grid;gap:var(--sp-3,12px);justify-items:center}.result-icon{width:64px;height:64px;color:var(--c-success)}.lead-sub{color:var(--c-text-2)}.summary{width:100%;display:grid;gap:var(--sp-2,8px)}.summary-name{font-size:var(--fs-md);color:var(--c-ink)}.phone{font-size:var(--fs-lg)}.company{overflow-wrap:anywhere}.actions{width:100%;display:grid;gap:var(--sp-3,12px);margin-top:var(--sp-2,8px)}</style>
