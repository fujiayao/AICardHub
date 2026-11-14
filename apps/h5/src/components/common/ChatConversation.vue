<script setup lang="ts">
import type { ChatMessage } from '@/composables/useChatStream'
import { nextTick, reactive, useTemplateRef, watch } from 'vue'
import { copyText } from '@/platform'
import { publicRefLabels } from '@/utils/kb-refs'
import MarkdownText from './MarkdownText.vue'

const props = defineProps<{ messages: ChatMessage[], sending?: boolean, staff?: boolean }>()
defineEmits<{ feedback: [message: ChatMessage], correction: [message: ChatMessage], retry: [] }>()
const scroller = useTemplateRef<HTMLElement>('scroller')
const expanded = reactive<Record<number, boolean>>({})
function longContent(content: string) { return content.split('\n').length > 10 || content.length > 420 }
function refLabels(refs: unknown[]) { return publicRefLabels(refs) }
watch(() => props.messages.map(m => m.content).join(''), async () => { await nextTick(); scroller.value?.scrollIntoView({ block: 'end', behavior: 'smooth' }) })
</script>
<template>
 <div class="conversation" role="log" aria-label="对话记录" aria-live="polite">
  <article v-for="message in messages" :key="message.id" class="message" :class="message.role">
   <div class="bubble">
    <span v-if="message.role === 'assistant'" class="ai-label">AI 分身</span>
    <div class="body" :class="{ collapsed: !expanded[message.id] && longContent(message.content) }">
     <MarkdownText v-if="message.role === 'assistant'" :text="message.content" />
     <p v-else class="preline user-text">{{ message.content }}</p>
     <span v-if="sending && message === messages.at(-1)" class="cursor">{{ message.content ? '' : '正在思考…' }}</span>
    </div>
    <button v-if="longContent(message.content)" class="text-button more" @click="expanded[message.id] = !expanded[message.id]">{{ expanded[message.id] ? '收起' : '展开全部' }}</button>
    <p v-if="message.failed" class="error">{{ message.interrupted ? '回答已中断，已保留收到的内容。请发送新问题。' : '回答失败，请重试' }}</p>
    <button v-if="message.failed && !message.interrupted" class="text-button" @click="$emit('retry')">重试回答</button>
   </div>
   <div v-if="message.role === 'assistant' && refLabels(message.kb_refs).length" class="refs" aria-label="引用来源">
    <span class="refs-label">引用</span>
    <span v-for="label in refLabels(message.kb_refs)" :key="label" class="ref-chip">{{ label }}</span>
   </div>
   <div v-if="message.role === 'assistant' && message.content" class="tools">
    <button class="text-button" :disabled="message.feedback" :aria-label="message.feedback ? '已反馈' : '点踩'" @click="$emit('feedback', message)">{{ message.feedback ? '已反馈' : '点踩' }}</button>
    <button class="text-button" aria-label="复制回答" @click="copyText(message.content)">复制</button>
    <button v-if="staff" class="text-button" @click="$emit('correction', message)">纠错</button>
   </div>
  </article>
  <div ref="scroller" />
 </div>
</template>
<style scoped>
.conversation{display:grid;gap:var(--sp-5);padding-bottom:var(--sp-5)}
.message{max-width:88%;justify-self:start;display:grid;gap:var(--sp-2)}
.message.user{justify-self:end}
.bubble{padding:var(--sp-3) var(--sp-4);background:var(--c-surface);border-radius:2px var(--r-lg) var(--r-lg);box-shadow:var(--sh-card)}
.user .bubble{background:var(--c-primary);color:var(--c-surface);border-radius:var(--r-lg) 2px var(--r-lg) var(--r-lg)}
.user-text{margin:0}
.ai-label{display:block;color:var(--c-ai);font-size:var(--fs-xs);font-weight:600;margin-bottom:var(--sp-2)}
.body.collapsed{max-height:240px;overflow:hidden;mask-image:linear-gradient(180deg,var(--c-ink) 72%,transparent)}
.more{padding-left:0}
.refs{display:flex;flex-wrap:wrap;align-items:center;gap:var(--sp-2)}
.refs-label{font-size:var(--fs-xs);color:var(--c-text-3)}
.ref-chip{display:inline-flex;align-items:center;padding:2px var(--sp-2);border-radius:var(--r-sm);background:var(--c-ai-soft);color:var(--c-ai);font-size:var(--fs-xs);border:1px solid var(--c-ai-line);max-width:100%;overflow-wrap:anywhere}
.tools{display:flex;gap:var(--sp-1)}
.tools button{font-size:var(--fs-xs);color:var(--c-text-2)}
.cursor{color:var(--c-ai)}
.cursor::after{content:'';display:inline-block;width:7px;height:15px;background:var(--c-ai);animation:blink 1s infinite;vertical-align:middle}
@keyframes blink{50%{opacity:.25}}
</style>
