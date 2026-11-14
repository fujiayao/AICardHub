<!-- 原型: A2 AI 对话 / A3 留资成功 -->
<script setup lang="ts">
import type { ChatMessage } from '@/composables/useChatStream'
import { showToast } from 'vant'
import { shallowRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError, errorMessage } from '@/api/client'
import { createSession, feedback, messages as getMessages, publicCard } from '@/api/generated'
import ChatComposer from '@/components/common/ChatComposer.vue'
import ChatConversation from '@/components/common/ChatConversation.vue'
import DemoBadge from '@/components/common/DemoBadge.vue'
import PhotoAvatar from '@/components/common/PhotoAvatar.vue'
import ResourceState from '@/components/common/ResourceState.vue'
import DisabledCard from '@/components/visitor/DisabledCard.vue'
import LeadSheet from '@/components/visitor/LeadSheet.vue'
import LeadSuccess from '@/components/visitor/LeadSuccess.vue'
import { useChatStream } from '@/composables/useChatStream'
import { useResource } from '@/composables/useResource'
import { callPhone } from '@/platform'
import { useVisitorStore } from '@/stores/visitor'
const route = useRoute('/chat/[code]'); const router = useRouter(); const code = String(route.params.code)
const visitor = useVisitorStore(); const sessionId = shallowRef<number>()
const lead = shallowRef(route.query.lead === '1')
const summary = shallowRef<{ name: string, phone: string, company_name: string }>()
const stream = useChatStream(() => `/api/v1/public/chat/sessions/${sessionId.value}/messages`)
const { messages, sending, error: chatError, model, leadPrompts } = stream
const { data, loading, error, reload } = useResource(async () => {
 const card = await publicCard({ path: { code } })
 if (card.status === 'disabled') return { card, opening: '', questions: [] }
 await visitor.ensure()
 const key = `shuke.chat.${code}`
 const remembered = Number(sessionStorage.getItem(key))
 if (remembered) {
  try { const history = await getMessages({ path: { id: remembered } }); messages.value = history.items; sessionId.value = remembered }
  catch (e) { if (!(e instanceof ApiError) || ![403, 404].includes(e.status)) throw e; sessionStorage.removeItem(key) }
 }
 let opening = card.assistant?.opening || ''; let questions = card.assistant?.guide_questions || []
 if (!sessionId.value) { const session = await createSession({ body: { card_code: code } }); sessionId.value = session.session_id; opening = session.opening; questions = session.guide_questions; sessionStorage.setItem(key, String(sessionId.value)) }
 if (typeof route.query.q === 'string') { const question = route.query.q; await router.replace({ path: route.path }); void stream.send(question) }
 return { card, opening, questions }
})
async function down(message: ChatMessage) {
 if (message.id < 0 || message.feedback) return
 try { await feedback({ path: { id: message.id }, body: { feedback: 'down' } }); message.feedback = true; showToast('感谢反馈') } catch (e) { showToast(errorMessage(e)) }
}
</script>
<template><ResourceState :loading="loading" :error="error" @retry="reload"><DisabledCard v-if="data?.card.status === 'disabled'" :company="data.card.company" /><LeadSuccess v-else-if="summary && data" :name="data.card.name || ''" :phone="data.card.mobile" :summary="summary" :code="code" @continue="summary = undefined" /><main v-else-if="data" class="page chat-page"><van-nav-bar :title="`${data.card.name}的 AI 分身`" left-arrow left-text="名片" @click-left="router.push(`/card/${code}`)"><template #right><button v-if="data.card.mobile" class="icon-button" aria-label="拨打电话" @click="callPhone(data.card.mobile)"><span class="icon i-lucide-phone" /></button></template></van-nav-bar><div class="content"><DemoBadge :model="model" /><section v-if="!messages.length" class="welcome stack"><PhotoAvatar :src="data.card.photo_url" :name="data.card.name || ''" :size="80" /><h2>你好，我是{{ data.card.name }}的 AI 分身</h2><p>{{ data.opening }}</p><p class="muted">你可以这样问我</p><van-button v-for="question in data.questions" :key="question" plain :disabled="sending" @click="stream.send(question)">{{ question }}</van-button></section><ChatConversation :messages="messages" :sending="sending" @feedback="down" @retry="stream.retry" /><p v-if="chatError" class="error" role="alert">{{ chatError }}</p><section v-for="(prompt, index) in leadPrompts" :key="index" class="panel stack"><h2>{{ prompt.title }}</h2><p class="muted">{{ prompt.reason }}</p><van-button plain @click="lead = true">留下联系方式</van-button><button v-if="data.card.mobile" class="text-button" @click="callPhone(data.card.mobile)">直接打电话</button></section><button class="text-button" @click="lead = true">留下联系方式</button></div><ChatComposer :disabled="!sessionId" :sending="sending" @send="stream.send" @stop="stream.stop" /><LeadSheet v-model="lead" :code="code" :session-id="sessionId" @submitted="summary = $event" /></main></ResourceState></template>
<style scoped>.chat-page{padding-bottom:140px;background:linear-gradient(180deg,var(--c-ai-soft),var(--c-bg) 350px)}.welcome{text-align:center;padding:28px 0}.welcome>.avatar{margin:auto}</style>
