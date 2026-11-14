<!-- 原型: B8 纠错记录 -->
<script setup lang="ts">
import { showConfirmDialog } from 'vant'
import { shallowRef } from 'vue'
import { corrections, deleteCorrection } from '@/api/generated'
import PageShell from '@/components/common/PageShell.vue'
import ResourceState from '@/components/common/ResourceState.vue'
import CorrectionSheet from '@/components/staff/CorrectionSheet.vue'
import { useMutation } from '@/composables/useMutation'
import { useResource } from '@/composables/useResource'
const show = shallowRef(false)
const { data, loading, error, reload } = useResource(() => corrections({ query: { page: 1, page_size: 100 } }))
const { failure, run } = useMutation()
async function remove(id: number) { try { await showConfirmDialog({ title: '删除纠错', message: '确定删除这条纠错记录？' }) } catch { return }; const result = await run(async () => { await deleteCorrection({ path: { id } }); return true }); if (result) reload() }
</script>
<template><PageShell title="纠错记录" back><template #action><button class="text-button" @click="show = true">新增</button></template><p class="ai-hint">纠错用于完善回答；对访客公开须经管理员批准。</p><p v-if="failure" class="error" role="alert">{{ failure }}</p><ResourceState :loading="loading" :error="error" :empty="!data?.items.length" empty-text="还没有纠错记录" @retry="reload"><article v-for="item in data?.items" :key="item.id" class="panel stack correction"><div class="row between c-head"><span class="source" :class="item.source">{{ item.source === 'test' ? '试聊' : item.source === 'visitor_chat' ? '客户对话' : '手动' }}</span><button class="text-button danger-button" @click="remove(item.id)">删除</button></div><div class="qa"><p class="q"><span class="qa-tag q-tag">问</span>{{ item.question }}</p><p class="a preline"><span class="qa-tag a-tag">答</span>{{ item.correct_answer }}</p></div><details v-if="item.wrong_answer"><summary class="muted small">原错误回答</summary><p class="preline error">{{ item.wrong_answer }}</p></details></article></ResourceState><CorrectionSheet v-model="show" @saved="reload" /></PageShell></template>
<style scoped>
.c-head{align-items:center}
.source{padding:2px 10px;border-radius:var(--r-sm);font-size:var(--fs-xs);background:var(--c-bg);color:var(--c-text-2)}
.source.test{background:var(--c-ai-soft);color:var(--c-ai)}
.source.visitor_chat{background:var(--c-primary-soft);color:var(--c-primary)}
.qa{display:grid;gap:var(--sp-2)}
.qa p{display:flex;gap:var(--sp-2);align-items:flex-start}
.qa-tag{flex-shrink:0;width:22px;height:22px;display:grid;place-items:center;border-radius:var(--r-sm);font-size:var(--fs-xs)}
.q-tag{background:var(--c-bg);color:var(--c-text-2)}
.a-tag{background:var(--c-success-soft);color:var(--c-success)}
.qa .a{color:var(--c-text)}
</style>
