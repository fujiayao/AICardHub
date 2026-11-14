<script setup lang="ts">
import type { ChatMessage } from '@/composables/useChatStream'
import { nextTick, shallowRef, useTemplateRef, watch } from 'vue'
import { copyText } from '@/platform'
const props = defineProps<{ messages: ChatMessage[], sending?: boolean, staff?: boolean }>()
defineEmits<{ feedback: [message: ChatMessage], correction: [message: ChatMessage], retry: [] }>()
const scroller = useTemplateRef<HTMLElement>('scroller')
const expanded = shallowRef(false)
watch(() => props.messages.map(m => m.content).join(''), async () => { await nextTick(); scroller.value?.scrollIntoView({ block: 'end', behavior: 'smooth' }) })
function refsText(refs: unknown[]) { return refs.map(ref => typeof ref === 'string' ? ref : ref && typeof ref === 'object' && 'title' in ref ? String(ref.title) : '知识资料').join('、') }
</script>
<template>
 <div class="conversation" role="log" aria-label="对话记录" aria-live="polite">
  <article v-for="message in messages" :key="message.id" class="message" :class="message.role">
   <div class="bubble">
<span v-if="message.role === 'assistant'" class="ai-label">AI 分身</span><p class="preline" :class="{ collapsed: !expanded && message.content.split('\n').length > 8 }">{{ message.content }}<span v-if="sending && message === messages.at(-1)" class="cursor">{{ message.content ? '' : '正在思考…' }}</span></p>
    <button v-if="message.content.split('\n').length > 8" class="text-button" @click="expanded = !expanded">{{ expanded ? '收起' : '展开全部' }}</button>
    <p v-if="message.failed" class="error">{{ message.interrupted ? '回答已中断，已保留收到的内容。请发送新问题。' : '回答失败，请重试' }}</p>
    <button v-if="message.failed && !message.interrupted" class="text-button" @click="$emit('retry')">重试回答</button>
   </div>
   <div v-if="message.role === 'assistant' && message.content" class="tools"><button class="text-button" :disabled="message.feedback" :aria-label="message.feedback ? '已反馈' : '点踩'" @click="$emit('feedback', message)">{{ message.feedback ? '已反馈' : '点踩' }}</button><button class="text-button" aria-label="复制回答" @click="copyText(message.content)">复制</button><button v-if="staff" class="text-button" @click="$emit('correction', message)">纠错</button></div>
   <p v-if="staff && message.kb_refs.length" class="muted small">引用：{{ refsText(message.kb_refs) }}</p>
  </article><div ref="scroller" />
 </div>
</template>
<style scoped>.conversation{display:grid;gap:20px;padding-bottom:20px}.message{max-width:88%;justify-self:start}.message.user{justify-self:end}.bubble{padding:14px 16px;background:var(--c-surface);border-radius:0 var(--r-lg) var(--r-lg);box-shadow:var(--sh-soft)}.user .bubble{background:var(--c-primary);color:var(--c-surface);border-radius:var(--r-lg) 0 var(--r-lg) var(--r-lg)}.ai-label{display:block;color:var(--c-ai);font-size:var(--fs-xs);font-weight:600;margin-bottom:6px}.tools{display:flex;gap:4px}.tools button{font-size:var(--fs-xs);color:var(--c-text-2)}.cursor{color:var(--c-ai)}.cursor::after{content:'';display:inline-block;width:7px;height:15px;background:var(--c-ai);animation:blink 1s infinite}.collapsed{max-height:220px;overflow:hidden}@keyframes blink{50%{opacity:.25}}</style>
