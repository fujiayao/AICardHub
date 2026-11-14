<script setup lang="ts">
// 原型: 名片原型-demo.html AI 消息区。暗色 scoped 命名（dk- 前缀）避免与全局 .msg/.ai 冲突。
import type { ChatMessage } from '@/composables/useChatStream'
import { computed } from 'vue'
import MarkdownText from '@/components/common/MarkdownText.vue'
import { publicRefLabels } from '@/utils/kb-refs'

const props = defineProps<{ messages: ChatMessage[], sending: boolean }>()
const emit = defineEmits<{ retry: [] }>()

const list = computed(() => props.messages.filter(m => m.role === 'user' || m.role === 'assistant'))
function refs(message: ChatMessage): string[] { return publicRefLabels(message.kb_refs) }
</script>

<template>
  <div class="dk-msgs" role="log" aria-label="对话记录" aria-live="polite">
    <div v-for="message in list" :key="message.id" class="dk-msg" :class="message.role === 'user' ? 'dk-me' : 'dk-ai'">
      <span class="dk-who">{{ message.role === 'user' ? '我' : 'AI' }}</span>
      <div class="dk-bubble">
        <MarkdownText v-if="message.content" :text="message.content" />
        <span v-if="message.role === 'assistant' && sending && !message.content" class="dk-cursor" aria-hidden="true" />
        <span v-if="message.role === 'assistant' && refs(message).length" class="dk-cite">
          <b>参考资料</b> · {{ refs(message).join(' · ') }}
        </span>
        <button v-if="message.failed && !message.interrupted" class="dk-retry" @click="emit('retry')">重试</button>
        <span v-else-if="message.interrupted" class="dk-note">回答已中断</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dk-msgs { flex: 1 0 auto; padding: 16px 22px 4px; display: flex; flex-direction: column; gap: 14px; }
.dk-msg { display: flex; gap: 8px; max-width: 100%; }
.dk-who {
  width: 24px; height: 24px; border-radius: 7px; flex: none; margin-top: 2px;
  display: grid; place-items: center; font-size: 10px; font-weight: 700;
}
.dk-ai .dk-who { background: var(--dk-mint-dim); color: var(--dk-mint); border: 1px solid var(--dk-avatar-ring); }
.dk-me { flex-direction: row-reverse; }
.dk-me .dk-who { background: var(--dk-surface-soft); color: var(--dk-role); }
.dk-bubble {
  font-size: 13.5px; line-height: 1.78; padding: 11px 14px; border-radius: 14px;
  max-width: calc(100% - 40px); word-break: break-word;
}
.dk-ai .dk-bubble { background: var(--dk-surface-2); border: 1px solid var(--dk-line); border-top-left-radius: 5px; color: var(--dk-bubble-ai); }
.dk-me .dk-bubble { background: var(--dk-mint-dim); border: 1px solid var(--dk-mint-line); border-top-right-radius: 5px; color: var(--dk-bubble-me); }
.dk-cite {
  display: block; margin-top: 9px; padding-top: 8px; border-top: 1px dashed var(--dk-cite-line);
  font-size: 10.5px; color: var(--dk-cite); letter-spacing: .01em;
}
.dk-cite b { color: var(--dk-cite-strong); font-weight: 600; }
.dk-cursor {
  display: inline-block; width: 6px; height: 14px; background: var(--dk-mint); vertical-align: -2px;
  animation: dk-blink .9s steps(1) infinite; margin-left: 2px;
}
.dk-retry { margin-top: 8px; border: 1px solid var(--dk-mint-line); background: transparent; color: var(--dk-mint); font-size: 11.5px; padding: 4px 12px; border-radius: 16px; cursor: pointer; }
.dk-note { display: block; margin-top: 6px; font-size: 10.5px; color: var(--dk-cite); }
.dk-ai .dk-bubble :deep(.md h4) { color: var(--dk-txt); }
.dk-ai .dk-bubble :deep(.md strong) { color: var(--dk-txt); }
@keyframes dk-blink { 0%, 100% { opacity: 1 } 50% { opacity: .25 } }
</style>
