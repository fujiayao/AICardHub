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
<template><PageShell title="客户详情" back><ResourceState :loading="loading" :error="error" @retry="reload"><template v-if="data?.lead"><section class="panel stack"><div class="row between"><h1>{{ data.lead.name }}</h1><span class="tag">{{ statusLabel(data.lead.status) }}</span></div><p class="num">{{ phoneLabel(data.lead.phone) }}</p><p v-if="data.lead.company_name">{{ data.lead.company_name }}</p><h2>需求描述</h2><p class="preline">{{ data.lead.need || '客户尚未填写需求' }}</p><p class="muted small">留资时间 {{ dateLabel(data.lead.created_at) }}</p></section><section class="panel stack"><h2>跟进备注</h2><p class="preline">{{ data.lead.remark || '暂无备注，点击标记状态添加' }}</p></section><p v-if="data.lead.session_id" class="muted">关联会话 #{{ data.lead.session_id }}。当前线索接口未提供访客编号，访客对话请从访客列表查看。</p><LeadStatusSheet v-model="status" :lead="data.lead" @saved="reload" /></template><template v-else-if="data?.visitor"><section class="panel stack"><h1>访客 #{{ data.visitor.anon_id.slice(-4) }}</h1><p class="muted">最近访问 {{ dateLabel(data.visitor.last_seen_at) }}</p><p class="ai-hint">该访客尚未从此入口提供联系方式</p></section><van-empty v-if="!data.visitor.sessions.length" description="该访客还没有对话" /><section v-for="session in data.visitor.sessions" :key="session.id" class="stack"><div class="panel stack"><h2>对话 #{{ session.id }}</h2><p class="ai-hint">{{ session.summary || '暂无 AI 摘要' }}</p></div><ChatConversation :messages="session.messages" staff @correction="correct($event, session.messages)" /></section></template></ResourceState><CorrectionSheet v-model="correcting" :question="question" :wrong-answer="selected?.content" :message-id="selected?.id" source="visitor_chat" /><template #footer><div v-if="data?.lead" class="bottom-bar"><button class="text-button" @click="copyText(data.lead.phone)">复制手机号</button><van-button @click="status = true">标记状态</van-button><van-button type="primary" @click="callPhone(data.lead.phone)">拨打电话</van-button></div></template></PageShell></template>
