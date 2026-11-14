<script setup lang="ts">
import type { NoteInput } from '@/api/generated'
import { reactive, watch } from 'vue'
const props = defineProps<{ initial?: { title: string, content: string }, saving?: boolean }>()
const emit = defineEmits<{ save: [note: NoteInput], cancel: [] }>()
const form = reactive({ title: '', content: '' })
watch(() => props.initial, value => { form.title = value?.title || ''; form.content = value?.content || '' }, { immediate: true })
function insert(value: string) { form.content += `\n${value}` }
</script>
<template><van-form class="stack note-editor" @submit="emit('save', { ...form, public: false, approved: false })"><van-cell-group inset><van-field v-model="form.title" label="标题" maxlength="200" placeholder="一篇只讲一个主题" :rules="[{ required: true, message: '请填写标题' }]" /></van-cell-group><p class="muted small help">标题写清主题；正文开头写一句简介，帮助 AI 理解适用范围。</p><div class="field-group"><div class="group-head"><p class="group-label">正文</p><div class="toolbar"><button type="button" class="chip-button" aria-label="插入标题" @click="insert('## ')">标题</button><button type="button" class="chip-button" aria-label="插入加粗" @click="insert('**内容**')">加粗</button><button type="button" class="chip-button" aria-label="插入列表" @click="insert('- ')">列表</button><button type="button" class="chip-button" aria-label="插入引用" @click="insert('> ')">引用</button></div></div><van-cell-group inset><van-field v-model="form.content" type="textarea" rows="12" autosize aria-label="正文" placeholder="正文内容" :rules="[{ required: true, message: '请填写正文' }]" /></van-cell-group></div><p v-if="form.content.length > 3000" class="notice">建议每篇控制在 3000 字以内，可拆分成多个主题。</p><p class="ai-hint">保存为私密草稿。管理员明确批准前，不会用于访客回答。</p><div class="actions"><van-button type="primary" block native-type="submit" :loading="saving">保存</van-button><van-button block @click="emit('cancel')">取消</van-button></div></van-form></template>
<style scoped>
.group-head{display:flex;align-items:center;justify-content:space-between;gap:var(--sp-2);padding:0 var(--sp-4) var(--sp-1);flex-wrap:wrap}
.group-label{font-size:var(--fs-sm);color:var(--c-text-2)}
.toolbar{display:flex;gap:var(--sp-1)}
.chip-button{min-height:28px;padding:0 10px;border:1px solid var(--c-line);border-radius:var(--r-sm);background:var(--c-surface);color:var(--c-text-2);font-size:var(--fs-xs)}
.help{padding:0 var(--sp-1)}
.actions{display:grid;gap:var(--sp-2);margin-top:var(--sp-2)}
</style>
