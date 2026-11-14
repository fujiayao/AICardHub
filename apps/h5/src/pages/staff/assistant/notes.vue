<!-- 原型: B6 个人知识列表 / 编辑 -->
<script setup lang="ts">
import type { NoteData, NoteInput } from '@/api/generated'
import { showConfirmDialog, showToast } from 'vant'
import { shallowRef } from 'vue'
import { createNote, deleteNote, notes, saveNote } from '@/api/generated'
import PageShell from '@/components/common/PageShell.vue'
import ResourceState from '@/components/common/ResourceState.vue'
import NoteEditor from '@/components/staff/NoteEditor.vue'
import { useMutation } from '@/composables/useMutation'
import { useResource } from '@/composables/useResource'
const { data, loading, error, reload } = useResource(() => notes({ query: { page: 1, page_size: 100 } }))
const editing = shallowRef(false); const selected = shallowRef<NoteData>()
const { saving, failure, run } = useMutation()
function edit(note?: NoteData) { selected.value = note; editing.value = true }
async function save(body: NoteInput) { const result = await run(() => selected.value ? saveNote({ path: { file_id: selected.value.file_id }, body: { ...body, public: selected.value.public, approved: false } }) : createNote({ body })); if (result) { editing.value = false; showToast('已保存为草稿'); reload() } }
async function remove(note: NoteData) { try { await showConfirmDialog({ title: '删除知识', message: `确定删除「${note.title}」？` }) } catch { return }; const result = await run(async () => { await deleteNote({ path: { file_id: note.file_id } }); return true }); if (result) reload() }
</script>
<template><PageShell :title="editing ? '编辑知识' : '个人知识'" back><template #action><button v-if="!editing" class="text-button" @click="edit()">新建</button></template><p class="ai-hint">一篇只讲一件事。个人知识默认私密，公开需管理员批准。</p><p v-if="failure" class="error" role="alert">{{ failure }}</p><NoteEditor v-if="editing" :initial="selected" :saving="saving" @save="save" @cancel="editing = false" /><template v-else><van-button block to="/staff/assistant/import">导入文档</van-button><ResourceState :loading="loading" :error="error" :empty="!data?.items.length" empty-text="还没有个人知识，点击新建添加" @retry="reload"><van-swipe-cell v-for="note in data?.items" :key="note.file_id"><article class="panel stack note"><button class="note-open" @click="edit(note)"><div class="row between note-head"><h2>{{ note.title }}</h2><span class="status" :class="note.public && note.approved ? 'open' : 'private'">{{ note.public && note.approved ? '已批准公开' : '私密 / 待批准' }}</span></div><p class="muted excerpt">{{ note.content.slice(0, 100) }}</p><p class="muted small meta">{{ note.content.length }} 字 · 修订 {{ note.revision }}</p></button></article><template #right><van-button square type="danger" @click="remove(note)">删除</van-button></template></van-swipe-cell></ResourceState></template></PageShell></template>
<style scoped>
.note-open{border:0;background:transparent;text-align:left;padding:0;width:100%;color:var(--c-text)}
.note-head{align-items:center;gap:var(--sp-2)}
.note-head h2{min-width:0;overflow-wrap:anywhere}
.status{flex-shrink:0;padding:2px 10px;border-radius:var(--r-sm);font-size:var(--fs-xs)}
.status.open{background:var(--c-success-soft);color:var(--c-success)}
.status.private{background:var(--c-bg);color:var(--c-text-2)}
.excerpt{margin-top:var(--sp-2)}
.meta{margin-top:var(--sp-1)}
</style>
