<script setup lang="ts">
import type { VisitorDetail, VisitorVisit } from '@/api/generated'
import { dateLabel } from '@/utils/format'

withDefaults(defineProps<{ visitor: VisitorDetail, showConversations?: boolean }>(), { showConversations: true })
const sources: Record<VisitorVisit['source'], string> = {
  nfc: 'NFC 碰一碰', qr: '扫码', poster: '海报', link: '链接', sig: '签名链接',
}
const intentLabels = { A: 'A 高意向', B: 'B 中意向', C: 'C 一般意向' }
</script>

<template>
  <section class="panel stack" aria-labelledby="customer-visits-title">
    <h2 id="customer-visits-title">访问轨迹</h2>
    <ol v-if="visitor.visits?.length" class="visits">
      <li v-for="(visit, index) in visitor.visits" :key="`${visit.created_at}-${index}`" class="visit">
        <h3>{{ sources[visit.source] }}</h3>
        <p class="muted small"><time :datetime="visit.created_at">{{ dateLabel(visit.created_at) }}</time> · 停留 <span class="num">{{ visit.stay_seconds }}</span> 秒</p>
      </li>
    </ol>
    <p v-else class="muted">暂无访问记录</p>
  </section>
  <template v-if="showConversations">
    <van-empty v-if="!visitor.sessions.length" description="该访客还没有对话" />
    <section v-for="session in visitor.sessions" :key="session.id" class="stack" :aria-label="`对话 ${session.id}`">
      <div class="panel stack">
        <div class="row between">
          <h2>对话 #{{ session.id }}</h2>
          <span v-if="session.intent_level" class="tag intent" :class="`intent-${session.intent_level}`">{{ intentLabels[session.intent_level] }}</span>
        </div>
        <p class="ai-hint preline">{{ session.summary || '暂无 AI 摘要' }}</p>
        <ul v-if="session.tags?.length" class="tags" aria-label="需求标签">
          <li v-for="(tag, index) in session.tags" :key="`${index}-${tag}`" class="tag">{{ tag }}</li>
        </ul>
      </div>
      <slot name="conversation" :session="session" />
    </section>
  </template>
</template>

<style scoped>
.visits{display:grid;gap:16px;margin:0;padding:0;list-style:none}
.visit{padding-bottom:12px;border-bottom:1px solid var(--c-line)}
.visit:last-child{padding-bottom:0;border-bottom:0}
.tags{display:flex;flex-wrap:wrap;gap:8px;margin:0;padding:0;list-style:none}
.intent{flex-shrink:0}
.intent-A{background:var(--c-amber-soft);color:var(--c-amber)}
.intent-C{background:var(--c-bg);color:var(--c-text-2)}
</style>
