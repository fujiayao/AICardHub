<script setup lang="ts">
import { shallowRef } from 'vue'
defineProps<{ disabled?: boolean, sending?: boolean }>()
const emit = defineEmits<{ send: [content: string], stop: [] }>()
const input = shallowRef('')
function send() { if (!input.value.trim()) return; emit('send', input.value); input.value = '' }
</script>
<template>
 <form class="chat-composer" @submit.prevent="send">
  <div class="field-row">
   <van-field v-model="input" label="消息" label-class="sr-only" placeholder="输入你想问的问题…" :maxlength="4000" :disabled="disabled || sending" @keydown.enter.exact.prevent="send" />
   <van-button v-if="sending" plain class="action" aria-label="停止回答" @click="$emit('stop')"><span class="icon i-lucide-square" aria-hidden="true" />停止</van-button>
   <van-button v-else type="primary" class="action" native-type="submit" :disabled="disabled || !input.trim()" aria-label="发送"><span class="icon i-lucide-send-horizontal" aria-hidden="true" /></van-button>
  </div>
  <p class="muted small">内容由 AI 生成，仅供参考，请以工作人员确认为准</p>
 </form>
</template>
<style scoped>
.chat-composer{position:fixed;bottom:0;left:0;right:0;max-width:480px;margin:auto;background:var(--c-surface);padding:var(--sp-3) var(--sp-4) calc(var(--sp-2) + env(safe-area-inset-bottom));z-index:10;border-top:1px solid var(--c-line);box-shadow:var(--sh-dock)}
.field-row{display:flex;align-items:center;gap:var(--sp-2)}
.van-field{flex:1;background:var(--c-bg);border-radius:var(--r-pill);padding-top:10px;padding-bottom:10px}
.action{flex-shrink:0;min-width:48px;height:44px;border-radius:var(--r-pill)}
.action .icon{width:18px;height:18px}
.action.van-button--primary.van-button--disabled{background:var(--c-line);border-color:var(--c-line);color:var(--c-text-3);opacity:1}
p{text-align:center;margin-top:var(--sp-2);color:var(--c-text-3)}
</style>
