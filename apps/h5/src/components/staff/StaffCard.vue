<script setup lang="ts">
import type { CardData } from '@/api/generated'
import { computed } from 'vue'
import AnonymousPortrait from '@/components/common/AnonymousPortrait.vue'
import PhotoAvatar from '@/components/common/PhotoAvatar.vue'
import { phoneLabel } from '@/utils/format'
const props = defineProps<{ card: CardData }>()
const role = computed(() => [props.card.display_title || props.card.title, props.card.dept].filter(Boolean).join('｜'))
const brand = computed(() => props.card.company_short_name || props.card.company_name || '')
</script>

<template>
  <section class="card-face">
    <div class="cf-top">
      <div class="cf-id">
        <div class="cf-name">{{ card.name }}</div>
        <div v-if="role" class="cf-title">{{ role }}</div>
      </div>
      <div class="cf-photo">
        <PhotoAvatar v-if="card.photo_url" :src="card.photo_url" :name="card.name" :size="64" />
        <AnonymousPortrait v-else />
      </div>
    </div>
    <div class="cf-info">
      <div v-if="card.mobile"><span class="icon i-lucide-phone" /><span class="num">{{ phoneLabel(card.mobile) }}</span></div>
      <div v-if="card.email"><span class="icon i-lucide-mail" />{{ card.email }}</div>
    </div>
    <div class="cf-brand">
      <span class="nfc-wave icon i-lucide-nfc" aria-hidden="true" />
      <span v-if="brand">{{ brand }}</span>
    </div>
  </section>
</template>

<style scoped>
.card-face {
  position: relative;
  height: 206px;
  border-radius: 18px;
  background: linear-gradient(135deg, var(--c-ink-2) 0%, var(--c-ink) 60%, var(--c-ink) 100%);
  color: var(--c-surface);
  overflow: hidden;
  padding: 20px;
  box-shadow: var(--sh-float);
}
.card-face::before {
  content: "";
  position: absolute;
  right: -60px;
  bottom: -80px;
  width: 240px;
  height: 240px;
  border-radius: var(--r-pill);
  border: 1px solid var(--c-on-ink-line);
}
.cf-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  position: relative;
}
.cf-name {
  font-size: var(--fs-xl);
  font-weight: 700;
  letter-spacing: .08em;
}
.cf-title {
  font-size: var(--fs-sm);
  color: var(--c-on-ink-2);
  margin-top: 4px;
}
.cf-photo {
  width: 64px;
  height: 64px;
  border-radius: var(--r-pill);
  overflow: hidden;
  border: 2px solid var(--c-on-ink-2);
  flex: none;
  background: linear-gradient(165deg, var(--c-hero-top), var(--c-ink));
}
.cf-info {
  position: absolute;
  left: 20px;
  bottom: 18px;
  font-size: var(--fs-xs);
  color: var(--c-on-ink-2);
  line-height: 1.9;
}
.cf-info div {
  display: flex;
  align-items: center;
  gap: 6px;
}
.cf-info .icon {
  width: 16px;
  height: 16px;
}
.cf-brand {
  position: absolute;
  right: 20px;
  bottom: 18px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-sm);
  font-weight: 600;
  letter-spacing: .1em;
}
.nfc-wave {
  width: 18px;
  height: 18px;
  color: var(--c-ai);
}
</style>
