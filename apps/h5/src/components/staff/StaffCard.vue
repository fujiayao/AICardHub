<script setup lang="ts">
import type { CardData } from '@/api/generated'
import PhotoAvatar from '@/components/common/PhotoAvatar.vue'
import { phoneLabel } from '@/utils/format'
defineProps<{ card: CardData }>()
</script>
<template><section class="staff-card"><div class="head"><div class="identity"><h2>{{ card.name }}</h2><p class="role">{{ card.display_title || card.title }}<span v-if="card.dept" class="sep">·</span>{{ card.dept }}</p></div><PhotoAvatar :src="card.photo_url" :name="card.name" :size="56" /></div><div class="contact"><p v-if="card.mobile" class="num">{{ phoneLabel(card.mobile) }}</p><p v-if="card.email" class="email">{{ card.email }}</p></div><div class="foot row between"><span class="chip">AI 智能名片</span><span class="org-mark row"><span class="icon i-lucide-nfc" aria-hidden="true" />数科</span></div></section></template>
<style scoped>
.staff-card{padding:var(--sp-5) var(--sp-5);background:linear-gradient(135deg,var(--c-ink),var(--c-ink-2));color:#fff;border-radius:var(--r-lg)}
.head{display:flex;justify-content:space-between;gap:var(--sp-4);align-items:flex-start}
.identity{min-width:0;flex:1}
.staff-card h2{font-size:var(--fs-xl);color:#fff;line-height:1.2;overflow-wrap:anywhere}
.role{font-size:var(--fs-sm);color:var(--c-on-ink-2);margin-top:var(--sp-2);overflow-wrap:anywhere}
.role .sep{margin:0 6px;opacity:.6}
.contact{margin:var(--sp-5) 0 var(--sp-4);display:grid;gap:4px}
.contact .num{font-size:var(--fs-md);letter-spacing:.5px}
.contact .email{font-size:var(--fs-sm);color:var(--c-on-ink-2);overflow-wrap:anywhere}
.foot{padding-top:var(--sp-3);border-top:1px solid var(--c-on-ink-line);font-size:var(--fs-xs)}
.chip{padding:2px 10px;border-radius:var(--r-sm);background:rgba(255,255,255,.14);color:#fff}
.org-mark{gap:4px;color:var(--c-on-ink-2)}
</style>
