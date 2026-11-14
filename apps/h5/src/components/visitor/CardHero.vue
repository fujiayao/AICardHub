<script setup lang="ts">
import type { PublicCard } from '@/api/generated'
import { computed } from 'vue'
import AnonymousPortrait from '@/components/common/AnonymousPortrait.vue'
import { share } from '@/platform'
const props = defineProps<{ card: PublicCard }>()
const origin = window.location.origin
const role = computed(() => [props.card.title, props.card.dept].filter(Boolean).join('｜'))
const brandName = computed(() => props.card.company.short_name || props.card.company.name)
function onShare() {
  share(`${props.card.name}｜${props.card.title}`, `${origin}/c/${props.card.code}?s=link`)
}
</script>

<template>
  <header class="vc-hero">
    <img v-if="card.photo_url" class="portrait" :src="card.photo_url" :alt="`${card.name}的职业照`">
    <AnonymousPortrait v-else class="portrait placeholder" />
    <div class="vc-top">
      <div class="logo-chip">
        <span class="logo-mark"><img v-if="card.company.logo_url" :src="card.company.logo_url" alt="" width="18"><span v-else class="icon i-lucide-hexagon" /></span>
        <span class="brand-name">{{ brandName }}</span>
      </div>
      <button class="glass" aria-label="分享名片" @click="onShare"><span class="icon i-lucide-share-2" /></button>
    </div>
    <div class="vc-id">
      <h1 class="vc-name">{{ card.name }}</h1>
      <p v-if="role" class="vc-title">{{ role }}</p>
      <p class="vc-co">{{ card.company.name }}</p>
    </div>
  </header>
</template>

<style scoped>
.vc-hero {
  position: relative;
  height: var(--hero-photo-h, 440px);
  flex: none;
  background: linear-gradient(165deg, var(--c-hero-top) 0%, var(--c-ink) 70%);
  overflow: hidden;
}
.portrait {
  position: absolute;
  left: 50%;
  bottom: 0;
  transform: translateX(-50%);
  height: 100%;
  width: auto;
  object-fit: cover;
  object-position: center top;
}
.portrait.placeholder {
  width: auto;
}
.vc-hero::after {
  content: "";
  position: absolute;
  inset: auto 0 0 0;
  height: 58%;
  background: linear-gradient(180deg, rgba(19, 41, 75, 0) 0%, rgba(19, 41, 75, .82) 62%, var(--c-ink) 100%);
}
.vc-top {
  position: absolute;
  top: 52px;
  left: 16px;
  right: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 2;
}
.logo-chip {
  display: flex;
  align-items: center;
  gap: var(--sp-2, 8px);
  color: var(--c-surface);
  font-weight: 600;
  font-size: var(--fs-sm);
  letter-spacing: .06em;
  min-width: 0;
}
.logo-mark {
  width: 28px;
  height: 28px;
  border-radius: var(--r-sm);
  background: var(--c-surface);
  color: var(--c-ink);
  display: grid;
  place-items: center;
  flex: none;
}
.logo-mark .icon {
  width: 18px;
  height: 18px;
}
.brand-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.glass {
  width: 36px;
  height: 36px;
  border-radius: var(--r-pill);
  background: rgba(255, 255, 255, .16);
  backdrop-filter: blur(8px);
  display: grid;
  place-items: center;
  color: var(--c-surface);
  flex: none;
}
.glass .icon {
  width: 18px;
  height: 18px;
}
.vc-id {
  position: absolute;
  left: 20px;
  right: 20px;
  bottom: 44px;
  z-index: 2;
  color: var(--c-surface);
}
.vc-name {
  font-size: var(--fs-xxl);
  font-weight: 700;
  letter-spacing: .06em;
  line-height: 1.2;
  color: var(--c-surface);
}
.vc-title {
  margin-top: 6px;
  font-size: var(--fs-base);
  color: var(--c-hero-id-title);
}
.vc-co {
  margin-top: 2px;
  font-size: var(--fs-sm);
  color: var(--c-hero-id-co);
  overflow-wrap: anywhere;
  word-break: break-word;
}
</style>
