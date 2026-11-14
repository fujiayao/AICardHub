<script setup lang="ts">
import type { CardData } from '@/api/generated'
import PhotoAvatar from '@/components/common/PhotoAvatar.vue'
import { phoneLabel } from '@/utils/format'
defineProps<{ card: CardData }>()
</script>
<template><section class="staff-card"><div class="row between"><div><h2>{{ card.name }}</h2><p>{{ card.display_title || card.title }} ｜ {{ card.dept }}</p></div><PhotoAvatar :src="card.photo_url" :name="card.name" :size="64" /></div><div class="contact"><p class="num">{{ phoneLabel(card.mobile) }}</p><p>{{ card.email }}</p></div><div class="row between"><span class="small">AI 智能名片</span><span class="row"><span class="icon i-lucide-nfc" aria-hidden="true" />数科</span></div></section></template>
<style scoped>.staff-card{padding:26px 24px;background:linear-gradient(120deg,var(--c-ink),var(--c-ink-2));color:var(--c-surface);border-radius:var(--r-lg)}.staff-card h2{font-size:var(--fs-xl);color:var(--c-surface)}.staff-card p{font-size:var(--fs-sm)}.contact{margin:24px 0}.small{opacity:.8}</style>
