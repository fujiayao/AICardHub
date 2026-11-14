<!-- 原型: B7 文档导入预览 -->
<script setup lang="ts">
import { showToast } from 'vant'
import { computed, ref, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { createNote, importNotes } from '@/api/generated'
import PageShell from '@/components/common/PageShell.vue'
import { useMutation } from '@/composables/useMutation'
const router = useRouter(); const file = shallowRef<File>(); const drafts = ref<{ title: string, content: string, checked: boolean, saved?: boolean }[]>([])
const { saving, failure, run } = useMutation()
const selected = computed(() => drafts.value.filter(d => d.checked && !d.saved))
async function choose(event: Event) {
 const chosen = (event.target as HTMLInputElement).files?.[0]; if (!chosen) return
 if (!/\.(?:pdf|docx)$/i.test(chosen.name) || chosen.size > 20 * 1024 * 1024) { showToast('支持 20MB 以内 PDF 或 Word 文档'); return }
 file.value = chosen; drafts.value = []; const body = new FormData(); body.append('file', chosen)
 const result = await run(() => importNotes({ body })); if (result) drafts.value = result.drafts.map(d => ({ ...d, checked: true }))
}
async function confirm() {
 const result = await run(async () => { for (const draft of selected.value) { await createNote({ body: { title: draft.title, content: draft.content, public: false, approved: false } }); draft.saved = true }; return true })
 if (result) { showToast('已保存为私密草稿'); router.push('/staff/assistant/notes') }
}
</script>
<template><PageShell title="导入文档" back><section class="panel stack"><label for="knowledge-file">选择 PDF / Word 文档</label><input id="knowledge-file" type="file" accept=".pdf,.docx" aria-label="导入文档" :disabled="saving" @change="choose"><p class="muted">单文件不超过 20MB，解析后先预览确认。</p><p v-if="file">{{ file.name }} · {{ (file.size / 1024).toFixed(1) }}KB</p><div v-if="saving" role="status"><van-loading size="20">正在处理，请稍候…</van-loading></div><p v-if="failure" role="alert" class="error">{{ failure }}。已保存的草稿不会重复入库，可继续提交剩余草稿。</p></section><p v-if="drafts.length" class="ai-hint">已整理为 {{ drafts.length }} 篇草稿，请确认。批准前不会用于访客回答。</p><van-empty v-if="file && !saving && !failure && !drafts.length" description="未解析出知识内容，可更换文档重试" /><article v-for="(draft, index) in drafts" :key="index" class="panel stack"><van-checkbox v-model="draft.checked" :disabled="draft.saved" :aria-label="`选择草稿${index + 1}`">{{ draft.saved ? '已入库' : `草稿 ${index + 1}` }}</van-checkbox><van-field v-model="draft.title" label="标题" :disabled="draft.saved" /><van-field v-model="draft.content" label="正文" type="textarea" autosize :disabled="draft.saved" /><button v-if="!draft.saved" class="text-button danger-button" @click="drafts.splice(index, 1)">删除草稿</button></article><template #footer><div v-if="drafts.length" class="bottom-bar"><van-button type="primary" :disabled="!selected.length || selected.some(d => !d.title.trim() || !d.content.trim())" :loading="saving" @click="confirm">确认入库（{{ selected.length }}）</van-button></div></template></PageShell></template>
