<script setup lang="ts">
import type { PublicCard } from '@/api/generated'
import { computed } from 'vue'
import AnonymousPortrait from '@/components/common/AnonymousPortrait.vue'
const props = defineProps<{ card: PublicCard }>()
const emit = defineEmits<{ chat: [question?: string] }>()
const opening = computed(() => props.card.assistant?.opening || (props.card.name ? `您好，我是${props.card.name}的 AI 分身，有什么可以帮您？` : '您好，有什么可以帮您？'))
const questions = computed(() => props.card.assistant?.guide_questions ?? [])
</script>

<template>
  <section class="ai-entry">
    <div class="ai-who">
      <span class="avatar avatar-ai">
        <img v-if="card.photo_url" :src="card.photo_url" :alt="`${card.name}的职业照`">
        <AnonymousPortrait v-else />
      </span>
      <div class="ai-who-text">
        <b>{{ card.name }}的 AI 分身</b>
        <div class="online">在线，随时为你解答</div>
      </div>
    </div>
    <p class="ai-say">{{ opening }}</p>
    <div v-if="questions.length" class="ai-qs">
      <button v-for="question in questions" :key="question" class="ai-q" @click="emit('chat', question)">
        <span class="ai-q-text">{{ question }}</span>
        <span class="icon i-lucide-chevron-right" />
      </button>
    </div>
    <button class="ai-ask" @click="emit('chat')">
      <span>问我任何关于{{ card.company.short_name || card.company.name }}的问题…</span>
      <i class="ai-ask-send"><span class="icon i-lucide-send" /></i>
    </button>
  </section>
</template>

<style scoped>
.ai-entry {
  margin: 0 16px;
  border-radius: 18px;
  background: var(--c-surface);
  padding: 16px;
  box-shadow: var(--sh-float);
  position: relative;
  overflow: hidden;
}
.ai-entry::before {
  content: "";
  position: absolute;
  right: -40px;
  top: -40px;
  width: 140px;
  height: 140px;
  border-radius: var(--r-pill);
  background: radial-gradient(circle, var(--c-ai-glow), var(--c-ai-glow-0) 70%);
}
.ai-who {
  display: flex;
  align-items: center;
  gap: 10px;
  position: relative;
}
.avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--r-pill);
  overflow: hidden;
  flex: none;
  background: linear-gradient(165deg, var(--c-hero-top), var(--c-ink));
  display: grid;
  place-items: center;
}
.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center top;
}
.avatar-ai {
  position: relative;
}
.avatar-ai::after {
  content: "";
  position: absolute;
  right: 0;
  bottom: 0;
  width: 28%;
  height: 28%;
  border-radius: var(--r-pill);
  background: var(--c-ai);
  border: 2px solid var(--c-surface);
}
.ai-who-text b {
  font-size: var(--fs-base);
  color: var(--c-ink);
}
.online {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: var(--fs-xs);
  color: var(--c-ai);
}
.online::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: var(--r-pill);
  background: var(--c-ai);
  box-shadow: 0 0 0 3px var(--c-ai-glow);
}
.ai-say {
  margin: 12px 0;
  padding: 10px 12px;
  border-radius: 4px 14px 14px 14px;
  background: var(--c-ai-soft);
  color: var(--c-ai-ink);
  font-size: var(--fs-base);
  line-height: 1.6;
  position: relative;
}
.ai-qs {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
  position: relative;
}
.ai-q {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 9px 12px;
  border: 0;
  border-radius: var(--r-md);
  background: var(--c-bg);
  font-size: var(--fs-sm);
  color: var(--c-ink);
  text-align: left;
  min-height: 44px;
  cursor: pointer;
}
.ai-q-text {
  flex: 1;
  min-width: 0;
}
.ai-q .icon {
  width: 16px;
  height: 16px;
  flex: none;
  color: var(--c-text-3);
}
.ai-ask {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-height: 46px;
  padding: 0 6px 0 16px;
  border-radius: 23px;
  border: 1.5px solid var(--c-ai);
  color: var(--c-text-3);
  font-size: var(--fs-base);
  position: relative;
  background: var(--c-surface);
  cursor: pointer;
}
.ai-ask span {
  flex: 1;
  text-align: left;
}
.ai-ask-send {
  width: 36px;
  height: 36px;
  border-radius: var(--r-pill);
  background: var(--c-ai);
  color: var(--c-surface);
  display: grid;
  place-items: center;
  flex: none;
}
.ai-ask-send .icon {
  width: 18px;
  height: 18px;
}
</style>
