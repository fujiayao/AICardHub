<script setup lang="ts">
import type { CompanyData } from '@/api/generated'
import { callPhone, openMap } from '@/platform'
defineProps<{ company: CompanyData }>()
</script>
<template><main class="content disabled-card"><span class="icon i-lucide-contact-round mark" aria-hidden="true" /><h1>该名片已停用</h1><p class="muted">您可以通过以下方式联系公司</p><section class="panel stack"><img v-if="company.logo_url" :src="company.logo_url" alt="公司标识" width="64"><h2>{{ company.name }}</h2><p v-if="company.phone">{{ company.phone }}</p><button v-if="company.address" class="text-button" @click="openMap(company.address)">{{ company.address }}</button></section><van-button v-if="company.phone" block type="primary" @click="callPhone(company.phone)">拨打公司电话</van-button><p v-else class="muted">公司尚未提供电话，请稍后重试。</p></main></template>
<style scoped>.disabled-card{padding-top:100px;text-align:center}.mark{width:64px;height:64px;color:var(--c-text-3);margin:auto}</style>
