<!-- 原型: B6 个人知识列表 / 编辑 -->
<script setup lang="ts">
import type { NoteData, NoteInput } from '@/api/generated'
import { showConfirmDialog, showToast } from 'vant'
import { shallowRef, useTemplateRef } from 'vue'
import { createNote, deleteNote, notes, saveNote } from '@/api/generated'
import PageShell from '@/components/common/PageShell.vue'
import ResourceState from '@/components/common/ResourceState.vue'
import NoteEditor from '@/components/staff/NoteEditor.vue'
import { useMutation } from '@/composables/useMutation'
import { useResource } from '@/composables/useResource'
import { dateLabel } from '@/utils/format'
const { data, loading, error, reload } = useResource(() => notes({ query: { page: 1, page_size: 100 } }))
const editing = shallowRef(false)
const selected = shallowRef<NoteData>()
const editor = useTemplateRef<InstanceType<typeof NoteEditor>>('editor')
const { saving, failure, run } = useMutation()
function edit(note?: NoteData) { selected.value = note; editing.value = true }
async function save(body: NoteInput) {
  const result = await run(() => selected.value
    ? saveNote({ path: { file_id: selected.value.file_id }, body: { ...body, public: selected.value.public, approved: false } })
    : createNote({ body }))
  if (result) { editing.value = false; showToast('已保存，下一次对话生效'); reload() }
}
async function remove(note: NoteData) {
  try { await showConfirmDialog({ title: '删除知识', message: `确定删除「${note.title}」？` }) }
  catch { return }
  const result = await run(async () => { await deleteNote({ path: { file_id: note.file_id } }); return true })
  if (result) reload()
}
</script>

<template>
  <PageShell :title="editing ? '编辑知识' : '个人知识'" back>
    <template v-if="editing" #action>
      <button class="text-button" :disabled="saving" @click="editor?.submit()">保存</button>
    </template>
    <template v-if="editing">
      <p v-if="failure" class="error" role="alert">{{ failure }}</p>
      <NoteEditor ref="editor" :initial="selected" @save="save" />
    </template>
    <template v-else>
      <div class="top-actions">
        <van-button type="primary" icon="plus" @click="edit()">新建</van-button>
        <van-button plain icon="description" to="/staff/assistant/import">导入文档</van-button>
      </div>
      <p class="ai-hint">一篇只讲一件事，标题和简介写清楚，AI 更容易找到。</p>
      <p v-if="failure" class="error" role="alert">{{ failure }}</p>
      <ResourceState :loading="loading" :error="error" :empty="!data?.items.length" empty-text="还没有个人知识，点击新建添加" @retry="reload">
        <div class="note-list">
          <van-swipe-cell v-for="note in data?.items" :key="note.file_id">
            <button class="note-item" @click="edit(note)">
              <span class="kb-ico" aria-hidden="true">MD</span>
              <span class="kb-main">
                <span class="kb-head">
                  <span class="kb-title">{{ note.title }}</span>
                  <span class="status" :class="note.public && note.approved ? 'open' : 'private'">{{ note.public && note.approved ? '已批准公开' : '私密 / 待批准' }}</span>
                </span>
                <span v-if="note.description" class="kb-desc">{{ note.description }}</span>
                <span class="kb-meta">
                  <span v-if="note.updated">{{ dateLabel(note.updated) }} 更新</span>
                  <span v-if="note.tokens">{{ note.tokens }} tokens</span>
                </span>
              </span>
            </button>
            <template #right>
              <van-button square type="danger" class="swipe-del" @click="remove(note)">删除</van-button>
            </template>
          </van-swipe-cell>
        </div>
        <p class="muted small swipe-hint">左滑可删除</p>
      </ResourceState>
    </template>
  </PageShell>
</template>

<style scoped>
.top-actions{display:grid;grid-template-columns:1fr 1fr;gap:var(--sp-3)}
.top-actions :deep(.van-button){width:100%}
.note-list{display:grid;gap:var(--sp-3)}
.note-item{display:flex;gap:var(--sp-3);width:100%;text-align:left;padding:var(--sp-4);border:0;background:var(--c-surface);border-radius:var(--r-lg);box-shadow:var(--sh-card);color:var(--c-text)}
.kb-ico{flex-shrink:0;width:36px;height:36px;display:grid;place-items:center;border-radius:var(--r-md);background:var(--c-primary-soft);color:var(--c-primary);font-size:var(--fs-xs);font-weight:700}
.kb-main{display:grid;gap:var(--sp-1);min-width:0;flex:1}
.kb-head{display:flex;align-items:center;gap:var(--sp-2);justify-content:space-between}
.kb-title{font-size:var(--fs-base);font-weight:600;color:var(--c-ink);min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.status{flex-shrink:0;padding:2px 10px;border-radius:var(--r-sm);font-size:var(--fs-xs)}
.status.open{background:var(--c-success-soft);color:var(--c-success)}
.status.private{background:var(--c-bg);color:var(--c-text-2)}
.kb-desc{font-size:var(--fs-sm);color:var(--c-text-2);display:-webkit-box;-webkit-line-clamp:2;line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.kb-meta{display:flex;gap:var(--sp-3);font-size:var(--fs-xs);color:var(--c-text-3)}
.swipe-del{height:100%}
.swipe-hint{text-align:center;padding:var(--sp-4)}
</style>
