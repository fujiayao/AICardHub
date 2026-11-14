<script setup lang="ts">
import type { NoteInput } from '@/api/generated'
import { reactive, watch } from 'vue'
const props = defineProps<{ initial?: { title: string, content: string }, saving?: boolean }>()
const emit = defineEmits<{ save: [note: NoteInput], cancel: [] }>()
const form = reactive({ title: '', content: '' })
watch(() => props.initial, value => { form.title = value?.title || ''; form.content = value?.content || '' }, { immediate: true })
function insert(value: string) { form.content += `\n${value}` }
</script>
<template><van-form class="stack" @submit="emit('save', { ...form, public: false, approved: false })"><van-field v-model="form.title" label="标题" maxlength="200" :rules="[{ required: true, message: '请填写标题' }]" /><p class="muted small">标题写清主题；正文开头写一句简介，帮助 AI 理解适用范围。</p><div class="row"><button type="button" class="text-button" aria-label="插入标题" @click="insert('## ')">标题</button><button type="button" class="text-button" aria-label="插入加粗" @click="insert('**内容**')">加粗</button><button type="button" class="text-button" aria-label="插入列表" @click="insert('- ')">列表</button><button type="button" class="text-button" aria-label="插入引用" @click="insert('> ')">引用</button></div><van-field v-model="form.content" label="正文" type="textarea" rows="12" autosize :rules="[{ required: true, message: '请填写正文' }]" /><p v-if="form.content.length > 3000" class="notice">建议每篇控制在 3000 字以内，可拆分成多个主题。</p><p class="ai-hint">保存为私密草稿。管理员明确批准前，不会用于访客回答。</p><van-button type="primary" block native-type="submit" :loading="saving">保存</van-button><van-button block @click="emit('cancel')">取消</van-button></van-form></template>
