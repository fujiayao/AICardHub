<script setup lang="ts">
import { shallowRef } from 'vue'
defineProps<{ disabled?: boolean, sending?: boolean }>()
const emit = defineEmits<{ send: [content: string], stop: [] }>()
const input = shallowRef('')
function send() { if (!input.value.trim()) return; emit('send', input.value); input.value = '' }
</script>
<template><form class="chat-composer" @submit.prevent="send"><div class="row"><van-field v-model="input" label="消息" label-class="sr-only" placeholder="问问我的 AI 分身…" :maxlength="4000" :disabled="disabled || sending" @keydown.enter.exact.prevent="send" /><van-button v-if="sending" plain aria-label="停止回答" @click="$emit('stop')">停止</van-button><van-button v-else type="primary" native-type="submit" :disabled="disabled || !input.trim()" aria-label="发送">发送</van-button></div><p class="muted small">内容由 AI 生成，仅供参考，请以工作人员确认为准</p></form></template>
<style scoped>.chat-composer{position:fixed;bottom:0;left:0;right:0;max-width:480px;margin:auto;background:var(--c-surface);padding:12px 16px calc(12px + env(safe-area-inset-bottom));z-index:10;border-top:1px solid var(--c-line)}.van-field{background:var(--c-bg);border-radius:var(--r-lg)}p{text-align:center;margin-top:6px}.van-button{flex-shrink:0}</style>
