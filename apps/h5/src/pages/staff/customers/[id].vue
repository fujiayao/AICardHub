<!-- 原型: B11 客户详情 / 状态标记 -->
<script setup lang="ts">
import type { LeadData, VisitorDetail } from '@/api/generated'
import type { ChatMessage } from '@/composables/useChatStream'
import { computed, shallowRef, watch } from 'vue'
import { useRoute } from 'vue-router'
import { lead as getLead, visitor as getVisitor } from '@/api/generated'
import ChatConversation from '@/components/common/ChatConversation.vue'
import PageShell from '@/components/common/PageShell.vue'
import PhotoAvatar from '@/components/common/PhotoAvatar.vue'
import ResourceState from '@/components/common/ResourceState.vue'
import CorrectionSheet from '@/components/staff/CorrectionSheet.vue'
import CustomerHistory from '@/components/staff/CustomerHistory.vue'
import LeadStatusSheet from '@/components/staff/LeadStatusSheet.vue'
import { useResource } from '@/composables/useResource'
import { callPhone, copyText } from '@/platform'
import { dateLabel, phoneLabel, sourceLabel, statusLabel } from '@/utils/format'
const route = useRoute('/staff/customers/[id]'); const isVisitor = computed(() => route.query.kind === 'visitor')
const status = shallowRef(false); const correcting = shallowRef(false); const selected = shallowRef<ChatMessage>(); const question = shallowRef('')
const { data, loading, error, reload } = useResource(async (): Promise<{ lead?: LeadData, visitor?: VisitorDetail }> => {
 const id = Number(route.params.id)
 return isVisitor.value ? { visitor: await getVisitor({ path: { id } }) } : { lead: await getLead({ path: { id } }) }
})
watch(() => route.fullPath, () => { data.value = undefined; status.value = false; reload() })
function correct(message: ChatMessage, records: ChatMessage[]) { selected.value = message; const index = records.findIndex(m => m.id === message.id); question.value = records.slice(0, index).reverse().find(m => m.role === 'user')?.content || ''; correcting.value = true }
</script>
<template><PageShell title="客户详情" back><ResourceState :loading="loading" :error="error" @retry="reload"><template v-if="data?.lead"><section class="v-head"><div class="l1"><PhotoAvatar :name="data.lead.name" :size="48" /><div class="l1-text"><b>{{ data.lead.name }}</b><div class="chips"><span class="status" :class="data.lead.status">{{ statusLabel(data.lead.status) }}</span></div></div></div><dl class="kv"><dt>手机</dt><dd class="num">{{ phoneLabel(data.lead.phone) }}</dd><template v-if="data.lead.company_name"><dt>公司</dt><dd>{{ data.lead.company_name }}</dd></template><dt>需求</dt><dd :class="{ 'kv-empty': !data.lead.need }">{{ data.lead.need || '客户尚未填写需求' }}</dd><template v-if="sourceLabel(data.lead.source)"><dt>来源</dt><dd>{{ sourceLabel(data.lead.source) }}｜{{ dateLabel(data.lead.created_at) }}</dd></template><template v-else><dt>留资</dt><dd>{{ dateLabel(data.lead.created_at) }}</dd></template></dl></section><section class="panel stack"><h2>跟进备注</h2><p class="preline" :class="{ 'empty-inline': !data.lead.remark }">{{ data.lead.remark || '暂无备注，点击标记状态添加' }}</p><p v-if="data.lead.session_id" class="muted small">关联会话 #{{ data.lead.session_id }}</p></section><router-link :to="`/staff/customers/${data.lead.visitor_id}?kind=visitor`" class="panel row between nav-row"><span>查看访客轨迹与对话</span><span class="icon i-lucide-chevron-right" aria-hidden="true" /></router-link><LeadStatusSheet v-model="status" :lead="data.lead" @saved="reload" /></template><template v-else-if="data?.visitor"><section class="v-head"><div class="l1"><PhotoAvatar :name="`#${data.visitor.anon_id.slice(-4)}`" :size="48" /><div class="l1-text"><b>访客 #{{ data.visitor.anon_id.slice(-4) }}</b><div class="chips"><span v-if="data.visitor.intent_level" class="lv" :class="`lv-${data.visitor.intent_level}`">{{ data.visitor.intent_level }}</span><span v-if="sourceLabel(data.visitor.source)" class="src">{{ sourceLabel(data.visitor.source) }}</span></div></div></div><dl class="kv"><dt>最近访问</dt><dd>{{ dateLabel(data.visitor.last_seen_at) }}</dd></dl><p class="muted small note">访客身份与联系方式分开管理；联系电话请在对应线索中查看。</p></section><CustomerHistory :visitor="data.visitor"><template #conversation="{ session }"><ChatConversation :messages="session.messages" staff @correction="correct($event, session.messages)" /></template></CustomerHistory></template></ResourceState><CorrectionSheet v-model="correcting" :question="question" :wrong-answer="selected?.content" :message-id="selected?.id" source="visitor_chat" /><template #footer><div v-if="data?.lead" class="bottom-bar actionbar"><button class="icon-button copy-btn" aria-label="复制手机号" @click="copyText(data.lead.phone)"><span class="icon i-lucide-copy" aria-hidden="true" /></button><van-button class="act-status" @click="status = true">标记状态</van-button><van-button type="primary" class="act-call" icon="phone-o" @click="callPhone(data.lead.phone)">拨打电话</van-button></div></template></PageShell></template>
<style scoped>
.v-head{background:var(--c-surface);border-radius:var(--r-lg);padding:16px}
.v-head .l1{display:flex;gap:12px;align-items:center}
.v-head .l1-text{flex:1;min-width:0}
.v-head .l1-text b{font-size:var(--fs-lg);color:var(--c-ink);overflow-wrap:anywhere}
.chips{display:flex;gap:6px;margin-top:4px;flex-wrap:wrap;align-items:center}
.kv{display:grid;grid-template-columns:auto 1fr;gap:6px 14px;margin-top:12px;font-size:var(--fs-sm)}
.kv dt{color:var(--c-text-3)}
.kv dd{margin:0;color:var(--c-text);overflow-wrap:anywhere}
.kv dd.kv-empty{color:var(--c-text-3)}
.note{margin-top:10px}
.status{flex-shrink:0;padding:3px 12px;border-radius:var(--r-sm);font-size:var(--fs-xs);background:var(--c-bg);color:var(--c-text-2)}
.status.new{background:var(--c-amber-soft);color:var(--c-amber)}
.status.contacted{background:var(--c-primary-soft);color:var(--c-primary)}
.status.converted{background:var(--c-success-soft);color:var(--c-success)}
.lv{flex-shrink:0;padding:3px 10px;border-radius:var(--r-sm);font-size:var(--fs-xs);font-weight:600;background:var(--c-bg);color:var(--c-text-2)}
.lv-A{background:var(--c-amber-soft);color:var(--c-amber)}
.lv-B{background:var(--c-primary-soft);color:var(--c-primary)}
.lv-C{background:var(--c-ai-soft);color:var(--c-ai)}
.src{font-size:var(--fs-xs);color:var(--c-text-3)}
.nav-row{color:var(--c-text);align-items:center}
.nav-row .icon{color:var(--c-text-3)}
.actionbar .copy-btn{flex:none;width:44px;background:var(--c-bg)}
.actionbar .act-status{flex:1}
.actionbar .act-call{flex:1.4}
</style>
