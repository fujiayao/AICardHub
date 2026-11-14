<script setup lang="ts">
import type { PublicCard } from '@/api/generated'
import { computed } from 'vue'
import IdentityMark from '@/components/common/IdentityMark.vue'
import { share } from '@/platform'
const props = defineProps<{ card: PublicCard }>()
const origin = window.location.origin
const role = computed(() => [props.card.title, props.card.dept].filter(Boolean).join(' ｜ '))
const companyChip = computed(() => props.card.company.short_name || props.card.company.name)
function onShare() {
  share(`${props.card.name}｜${props.card.title}`, `${origin}/c/${props.card.code}?s=link`)
}
</script>

<template>
  <header class="hero" :class="{ photo: card.photo_url }">
    <img v-if="card.photo_url" class="portrait" :src="card.photo_url" :alt="`${card.name}的职业照`">
    <div v-if="card.photo_url" class="shade" />
    <div class="hero-top row between">
      <div class="brand row">
        <img v-if="card.company.logo_url" :src="card.company.logo_url" alt="公司标识" width="24">
        <span class="brand-name">{{ companyChip }}</span>
      </div>
      <button class="share icon-button" aria-label="分享名片" @click="onShare">
        <span class="icon i-lucide-share-2" />
      </button>
    </div>
    <div class="identity" :class="{ compact: !card.photo_url }">
      <div v-if="!card.photo_url" class="mark"><IdentityMark :name="card.name" :size="64" /></div>
      <h1>{{ card.name }}</h1>
      <p v-if="role" class="role">{{ role }}</p>
      <p class="company">{{ card.company.name }}</p>
    </div>
  </header>
</template>

<style scoped>
.hero {
  position: relative;
  background: linear-gradient(160deg, var(--c-ink) 0%, var(--c-ink-2) 100%);
  color: var(--c-surface);
  overflow: hidden;
}
.hero.photo {
  height: var(--hero-photo-h, 420px);
  background: var(--c-ink);
}
.portrait,
.shade {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center top;
}
.shade {
  background: linear-gradient(180deg, transparent 32%, var(--c-ink) 100%);
}
.hero-top {
  position: relative;
  padding: var(--sp-4, 16px);
  gap: var(--sp-2, 8px);
}
.brand {
  min-width: 0;
  gap: var(--sp-2, 8px);
}
.brand-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--fs-sm);
}
.share {
  flex-shrink: 0;
  background: var(--c-ink-2);
  color: var(--c-surface);
}
.identity {
  position: relative;
}
.hero.photo .identity {
  position: absolute;
  bottom: 54px;
  left: var(--sp-6, 24px);
  right: var(--sp-6, 24px);
}
.identity.compact {
  padding: var(--sp-4, 16px) var(--sp-6, 24px) 56px;
  min-width: 0;
}
.identity.compact :deep(.avatar),
.identity.compact .mark {
  margin-bottom: var(--sp-5, 20px);
}
.identity h1 {
  font-size: var(--fs-xxl);
  line-height: 1.2;
  color: var(--c-surface);
}
.identity .role {
  margin-top: 4px;
  font-size: var(--fs-md);
  color: var(--c-surface);
  opacity: .9;
}
.identity .company {
  margin-top: 6px;
  font-size: var(--fs-sm);
  color: var(--c-surface);
  opacity: .72;
  overflow-wrap: anywhere;
  word-break: break-word;
  max-width: 100%;
}
.identity.compact .role {
  margin-top: 0;
}
</style>
