<script setup lang="ts">
// B5 AI 状态卡：青绿渐变 + 三个指标（本周回答/没答上来/被点踩）。
// 指标来自 GET /me/assistant/metrics（me_assistant_metrics），均为真实统计。
import type { AssistantMetrics } from '@/api/generated'
import AnonymousPortrait from '@/components/common/AnonymousPortrait.vue'
defineProps<{
  templateName?: string
  metrics?: AssistantMetrics
}>()
</script>

<template>
  <section class="ai-status">
    <div class="top">
      <span class="ai-avatar"><AnonymousPortrait /></span>
      <div class="top-text">
        <b>AI 分身运行中</b>
        <span>{{ templateName ? `使用「${templateName}」模板，公司知识已同步` : '公司知识已同步' }}</span>
      </div>
    </div>
    <div class="nums">
      <div><b>{{ metrics?.answers ?? 0 }}</b>本周回答</div>
      <div><b>{{ metrics?.unanswered ?? 0 }}</b>没答上来</div>
      <div><b>{{ metrics?.disliked ?? 0 }}</b>被点踩</div>
    </div>
  </section>
</template>

<style scoped>
.ai-status {
  border-radius: 18px;
  padding: 16px;
  background: linear-gradient(140deg, var(--c-ai) 0%, var(--c-ai-ink) 100%);
  color: var(--c-surface);
  position: relative;
  overflow: hidden;
}
.ai-status::after {
  content: "";
  position: absolute;
  right: -30px;
  top: -30px;
  width: 130px;
  height: 130px;
  border-radius: var(--r-pill);
  background: var(--c-on-ink-line);
}
.top {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
  z-index: 1;
}
.ai-avatar {
  width: 44px;
  height: 44px;
  border-radius: var(--r-pill);
  overflow: hidden;
  flex: none;
  background: linear-gradient(165deg, var(--c-hero-top), var(--c-ink));
  display: grid;
  place-items: center;
}
.top-text b {
  display: block;
  font-size: var(--fs-md);
}
.top-text span {
  font-size: var(--fs-xs);
  color: var(--c-ai-soft);
}
.nums {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  margin-top: 14px;
  position: relative;
  z-index: 1;
}
.nums div {
  font-size: 11px;
  color: var(--c-ai-soft);
}
.nums b {
  display: block;
  font-family: var(--font-num);
  font-size: 22px;
  color: var(--c-surface);
  line-height: 1.3;
}
</style>
