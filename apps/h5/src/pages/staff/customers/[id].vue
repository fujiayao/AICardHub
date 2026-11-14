<!-- 原型: B11 客户详情 / 状态标记 -->
<script setup lang="ts">
import type { LeadData, VisitorDetail } from '@/api/generated'
import type { ChatMessage } from '@/composables/useChatStream'
import { computed, shallowRef, watch } from 'vue'
import { useRoute } from 'vue-router'
import { lead as getLead, visitor as getVisitor } from '@/api/generated'
import ChatConversation from '@/components/common/ChatConversation.vue'
import PageShell from '@/components/common/PageShell.vue'
import ResourceState from '@/components/common/ResourceState.vue'
import CorrectionSheet from '@/components/staff/CorrectionSheet.vue'
import CustomerHistory from '@/components/staff/CustomerHistory.vue'
import LeadStatusSheet from '@/components/staff/LeadStatusSheet.vue'
import { useResource } from '@/composables/useResource'
import { callPhone, copyText } from '@/platform'
import { dateLabel, phoneLabel, statusLabel } from '@/utils/format'
const route = useRoute('/staff/customers/[id]'); const isVisitor = computed(() => route.query.kind === 'visitor')
const status = shallowRef(false); const correcting = shallowRef(false); const selected = shallowRef<ChatMessage>(); const question = shallowRef('')
const { data, loading, error, reload } = useResource(async (): Promise<{ lead?: LeadData, visitor?: VisitorDetail }> => {
 const id = Number(route.params.id)
 return isVisitor.value ? { visitor: await getVisitor({ path: { id } }) } : { lead: await getLead({ path: { id } }) }
})
watch(() => route.fullPath, () => { data.value = undefined; status.value = false; reload() })
function correct(message: ChatMessage, records: ChatMessage[]) { selected.value = message; const index = records.findIndex(m => m.id === message.id); question.value = records.slice(0, index).reverse().find(m => m.role === 'user')?.content || ''; correcting.value = true }
</script>
<template><PageShell title="客户详情" back><ResourceState :loading="loading" :error="error" @retry="reload"><template v-if="data?.lead"><section class="panel stack lead-head"><div class="row between head"><h1>{{ data.lead.name }}</h1><span class="status" :class="data.lead.status">{{ statusLabel(data.lead.status) }}</span></div><p class="num phone">{{ phoneLabel(data.lead.phone) }}</p><p v-if="data.lead.company_name" class="muted company">{{ data.lead.company_name }}</p><p class="muted small">留资时间 {{ dateLabel(data.lead.created_at) }}</p></section><section class="panel stack"><h2>需求描述</h2><p class="preline" :class="{ 'empty-inline': !data.lead.need }">{{ data.lead.need || '客户尚未填写需求' }}</p></section><section class="panel stack"><h2>跟进备注</h2><p class="preline" :class="{ 'empty-inline': !data.lead.remark }">{{ data.lead.remark || '暂无备注，点击标记状态添加' }}</p><p v-if="data.lead.session_id" class="muted small">关联会话 #{{ data.lead.session_id }}</p></section><router-link :to="`/staff/customers/${data.lead.visitor_id}?kind=visitor`" class="panel row between nav-row"><span>查看访客轨迹与对话</span><span class="icon i-lucide-chevron-right" aria-hidden="true" /></router-link><LeadStatusSheet v-model="status" :lead="data.lead" @saved="reload" /></template><template v-else-if="data?.visitor"><section class="panel stack"><h1>访客 #{{ data.visitor.anon_id.slice(-4) }}</h1><p class="muted">最近访问 {{ dateLabel(data.visitor.last_seen_at) }}</p><p class="muted small">访客身份与联系方式分开管理；联系电话请在对应线索中查看。</p></section><CustomerHistory :visitor="data.visitor"><template #conversation="{ session }"><ChatConversation :messages="session.messages" staff @correction="correct($event, session.messages)" /></template></CustomerHistory></template></ResourceState><CorrectionSheet v-model="correcting" :question="question" :wrong-answer="selected?.content" :message-id="selected?.id" source="visitor_chat" /><template #footer><div v-if="data?.lead" class="bottom-bar"><button class="text-button" @click="copyText(data.lead.phone)">复制手机号</button><van-button @click="status = true">标记状态</van-button><van-button type="primary" @click="callPhone(data.lead.phone)">拨打电话</van-button></div></template></PageShell></template>
<style scoped>
.head{align-items:center;gap:var(--sp-2)}
.head h1{min-width:0;overflow-wrap:anywhere}
.phone{font-size:var(--fs-md);margin-top:var(--sp-1)}
.company{overflow-wrap:anywhere}
.status{flex-shrink:0;padding:3px 12px;border-radius:var(--r-sm);font-size:var(--fs-xs);background:var(--c-bg);color:var(--c-text-2)}
.status.new{background:var(--c-amber-soft);color:var(--c-amber)}
.status.contacted{background:var(--c-primary-soft);color:var(--c-primary)}
.status.converted{background:var(--c-success-soft);color:var(--c-success)}
.nav-row{color:var(--c-text);align-items:center}
.nav-row .icon{color:var(--c-text-3)}
</style>
