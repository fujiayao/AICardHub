<!-- 原型: B5 AI 助手 -->
<script setup lang="ts">
import type { AssistantInput } from '@/api/generated'
import { showToast } from 'vant'
import { computed, shallowRef } from 'vue'
import { assistant as getAssistant, templates as getTemplates, profile, saveAssistant } from '@/api/generated'
import DemoBadge from '@/components/common/DemoBadge.vue'
import ResourceState from '@/components/common/ResourceState.vue'
import AssistantEditor from '@/components/staff/AssistantEditor.vue'
import StaffShell from '@/components/staff/StaffShell.vue'
import { useMutation } from '@/composables/useMutation'
import { useResource } from '@/composables/useResource'
const showTemplates = shallowRef(false); const custom = shallowRef('')
const { data, loading, error, reload } = useResource(async () => { const [assistant, templates, staff] = await Promise.all([getAssistant(), getTemplates(), profile()]); return { assistant, templates, staff } })
const { saving, failure, run } = useMutation()
const current = computed(() => data.value?.templates.find(t => t.id === data.value?.assistant.template_id))
const questions = computed(() => data.value?.assistant.guide_questions || [])
async function save(part: Partial<AssistantInput>) {
 if (!data.value) return
 const result = await run(() => saveAssistant({ body: { ...data.value!.assistant, ...part } }))
 if (result) { data.value = { ...data.value, assistant: result }; showTemplates.value = false; showToast('已保存') }
}
function preview(value: string) { const staff = data.value?.staff; return value.replaceAll('{姓名}', staff?.name || '').replaceAll('{职位}', staff?.title || '').replaceAll('{部门}', staff?.dept || '').replaceAll('{负责业务}', staff?.business_scope || '') }
function addQuestion() { if (!custom.value.trim() || questions.value.length >= 3) return; void save({ guide_questions: [...questions.value, custom.value.trim()] }); custom.value = '' }
</script>
<template><StaffShell title="AI 助手"><template #action><van-button size="small" class="ai-button" to="/staff/assistant/test">试聊</van-button></template><ResourceState :loading="loading" :error="error" @retry="reload"><template v-if="data"><section class="ai-header"><span class="ai-avatar icon i-lucide-sparkles" aria-hidden="true" /><div class="ai-head-text"><h2>管理我的 AI 分身</h2><p>配置保存后即时生效</p></div></section><DemoBadge /><p v-if="failure" class="error" role="alert">{{ failure }}</p><section class="panel stack"><h2>人设模板</h2><h3>{{ current?.name || '尚未选择模板' }}</h3><p class="muted preline">{{ current ? preview(current.persona || '') : '选择管理员提供的模板' }}</p><van-button plain @click="showTemplates = true">切换模板</van-button></section><AssistantEditor title="个人补充" field="persona_extra" :value="data.assistant.persona_extra || ''" :saving="saving" @save="save({ persona_extra: $event })" /><AssistantEditor title="开场白" field="opening" :value="data.assistant.opening || ''" :saving="saving" @save="save({ opening: $event })" /><section class="panel stack"><h2>引导问题 <span class="muted">{{ questions.length }}/3</span></h2><div v-for="(question, index) in questions" :key="question" class="row between"><p>{{ question }}</p><button class="icon-button" :aria-label="`删除引导问题${index + 1}`" :disabled="saving" @click="save({ guide_questions: questions.filter((_, i) => i !== index) })"><span class="icon i-lucide-x" /></button></div><van-field v-model="custom" label="新增问题" maxlength="20" placeholder="最多 20 字"><template #button><van-button size="small" :disabled="questions.length >= 3 || !custom.trim() || saving" @click="addQuestion">添加</van-button></template></van-field><template v-for="question in current?.guide_questions" :key="question"><button v-if="!questions.includes(question)" class="text-button" :disabled="questions.length >= 3 || saving" @click="save({ guide_questions: [...questions, question] })">{{ question }}</button></template></section><van-cell-group inset><van-cell title="个人知识" label="个人笔记默认私密，公开须经管理员批准" is-link to="/staff/assistant/notes" /><van-cell title="纠错记录" is-link to="/staff/assistant/corrections" /></van-cell-group><p class="muted small">公司知识由管理员统一维护。个人知识和纠错是否可用于访客回答，以管理员批准为准。</p><van-popup v-model:show="showTemplates" position="bottom" round closeable><section class="sheet stack"><h2>选择模板</h2><van-empty v-if="!data.templates.length" description="管理员尚未配置模板" /><button v-for="template in data.templates" :key="template.id" class="template-option" :disabled="saving" @click="save({ template_id: template.id })"><h3>{{ template.name }}</h3><p class="muted preline">{{ preview(template.persona || '') }}</p></button></section></van-popup></template></ResourceState></StaffShell></template>
<style scoped>.ai-header{display:flex;align-items:center;gap:var(--sp-3);padding:var(--sp-4);background:var(--c-ai-soft);border:1px solid var(--c-ai-line);border-radius:var(--r-lg)}.ai-avatar{display:grid;place-items:center;width:44px;height:44px;border-radius:var(--r-md);background:var(--c-ai);color:#fff;font-size:22px;flex-shrink:0}.ai-head-text h2{color:var(--c-ai)}.ai-head-text p{font-size:var(--fs-sm);color:var(--c-text-2);margin-top:2px}.ai-button{background:var(--c-ai);color:var(--c-surface);border-color:var(--c-ai)}.template-option{padding:16px;text-align:left;border:1px solid var(--c-line);border-radius:var(--r-md);background:var(--c-surface)}</style>
