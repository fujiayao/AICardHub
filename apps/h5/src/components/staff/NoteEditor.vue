<script setup lang="ts">
import type { NoteInput } from '@/api/generated'
import { showToast } from 'vant'
import { reactive, watch } from 'vue'
const props = defineProps<{ initial?: { title: string, description?: string, content: string } }>()
const emit = defineEmits<{ save: [note: NoteInput] }>()
const form = reactive({ title: '', description: '', content: '' })
watch(() => props.initial, (value) => { form.title = value?.title || ''; form.description = value?.description || ''; form.content = value?.content || '' }, { immediate: true })
function insert(value: string) { form.content += form.content ? `\n${value}` : value }
function submit() {
  if (!form.title.trim() || !form.content.trim()) { showToast('请填写标题和正文'); return }
  const note: NoteInput = { title: form.title, content: form.content, public: false, approved: false }
  // 简介留空时不下发 description，避免覆盖后端已有简介
  const description = form.description.trim()
  if (description) note.description = description
  emit('save', note)
}
defineExpose({ submit })
</script>

<template>
  <van-form class="stack note-editor" @submit="submit">
    <van-cell-group inset>
      <van-field v-model="form.title" label="标题" maxlength="200" placeholder="一篇只讲一个主题" :rules="[{ required: true, message: '请填写标题' }]" />
    </van-cell-group>
    <div class="field-group">
      <p class="group-label intro-label">简介<small>AI 用它判断何时引用</small></p>
      <van-cell-group inset>
        <van-field v-model="form.description" type="textarea" rows="2" autosize maxlength="80" show-word-limit aria-label="简介" placeholder="一句话说明这篇讲什么、客户问到什么时引用" />
      </van-cell-group>
    </div>
    <div class="field-group">
      <div class="group-head">
        <p class="group-label">正文</p>
        <div class="toolbar">
          <button type="button" class="chip-button" aria-label="插入标题" @click="insert('## ')">H</button>
          <button type="button" class="chip-button" aria-label="插入加粗" @click="insert('**内容**')">B</button>
          <button type="button" class="chip-button" aria-label="插入列表" @click="insert('- ')"><span class="icon i-lucide-list" aria-hidden="true" /></button>
          <button type="button" class="chip-button" aria-label="插入引用" @click="insert('> ')">“</button>
          <span class="md-flag">Markdown</span>
        </div>
      </div>
      <van-cell-group inset>
        <van-field v-model="form.content" type="textarea" rows="12" autosize aria-label="正文" placeholder="正文内容" :rules="[{ required: true, message: '请填写正文' }]" />
      </van-cell-group>
    </div>
    <p v-if="form.content.length > 3000" class="notice">建议一篇只讲一件事，≤ 3000 字，可拆分成多个主题。</p>
    <p class="ai-hint">保存为私密草稿。管理员明确批准前，不会用于访客回答。</p>
  </van-form>
</template>

<style scoped>
.field-group{display:grid;gap:var(--sp-1)}
.group-head{display:flex;align-items:center;justify-content:space-between;gap:var(--sp-2);padding:0 var(--sp-4) var(--sp-1);flex-wrap:wrap}
.group-label{font-size:var(--fs-sm);color:var(--c-text-2);padding:0 var(--sp-4)}
.group-head .group-label{padding:0}
.intro-label small{margin-left:var(--sp-2);color:var(--c-text-3);font-size:var(--fs-xs)}
.toolbar{display:flex;align-items:center;gap:var(--sp-1)}
.chip-button{min-width:30px;min-height:28px;padding:0 8px;border:1px solid var(--c-line);border-radius:var(--r-sm);background:var(--c-surface);color:var(--c-text-2);font-size:var(--fs-sm);display:inline-flex;align-items:center;justify-content:center}
.chip-button .icon{width:16px;height:16px}
.md-flag{margin-left:var(--sp-1);font-size:var(--fs-xs);color:var(--c-text-3)}
</style>
