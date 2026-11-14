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
import IdentityMark from '@/components/common/IdentityMark.vue'
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
<template><ResourceState :loading="loading" :error="error" @retry="reload"><DisabledCard v-if="data?.card.status === 'disabled'" :company="data.card.company" /><LeadSuccess v-else-if="summary && data" :name="data.card.name || ''" :phone="data.card.mobile" :summary="summary" :code="code" @continue="summary = undefined" /><main v-else-if="data" class="page chat-page"><van-nav-bar :title="`${data.card.name}的 AI 分身`" left-arrow left-text="名片" @click-left="router.push(`/card/${code}`)"><template #right><button v-if="data.card.mobile" class="icon-button" aria-label="拨打电话" @click="callPhone(data.card.mobile)"><span class="icon i-lucide-phone" /></button></template></van-nav-bar><div class="content"><DemoBadge :model="model" /><section v-if="!messages.length" class="welcome"><PhotoAvatar v-if="data.card.photo_url" :src="data.card.photo_url" :name="data.card.name || ''" :size="80" /><IdentityMark v-else :name="data.card.name" :size="80" /><h2>你好，我是{{ data.card.name }}的 AI 分身</h2><p class="opening">{{ data.opening }}</p><p v-if="data.questions.length" class="muted hint">你可以这样问我</p><div class="chips"><button v-for="question in data.questions" :key="question" class="chip" :disabled="sending" @click="stream.send(question)">{{ question }}<span class="icon i-lucide-chevron-right" /></button></div></section><ChatConversation :messages="messages" :sending="sending" @feedback="down" @retry="stream.retry" /><p v-if="chatError" class="error" role="alert">{{ chatError }}</p><section v-for="(prompt, index) in leadPrompts" :key="index" class="panel lead-card"><div class="row"><span class="icon i-lucide-user-plus lead-icon" /><h2>{{ prompt.title }}</h2></div><p class="muted">{{ prompt.reason }}</p><van-button block type="primary" @click="lead = true">留下联系方式</van-button><button v-if="data.card.mobile" class="text-button" @click="callPhone(data.card.mobile)">直接打电话</button></section><button class="text-button leave" @click="lead = true">留下联系方式</button></div><ChatComposer :disabled="!sessionId" :sending="sending" @send="stream.send" @stop="stream.stop" /><LeadSheet v-model="lead" :code="code" :session-id="sessionId" @submitted="summary = $event" /></main></ResourceState></template>
<style scoped>.chat-page{padding-bottom:140px;background:linear-gradient(180deg,var(--c-ai-soft),var(--c-bg) 350px)}.welcome{text-align:center;padding:28px 0;display:grid;justify-items:center;gap:var(--sp-2,8px)}.welcome .opening{color:var(--c-text-2);max-width:88%}.welcome .hint{margin-top:var(--sp-2,8px)}.welcome .chips{display:grid;gap:var(--sp-2,8px);width:100%;margin-top:var(--sp-1,4px)}.welcome .chip{display:flex;justify-content:space-between;align-items:center;gap:var(--sp-2,8px);text-align:left;min-height:44px;padding:10px 14px;border:1px solid var(--c-ai-line,var(--c-line));background:var(--c-surface);border-radius:var(--r-md);color:var(--c-ink);font-size:var(--fs-sm)}.welcome .chip:disabled{opacity:.5}.welcome .chip .icon{width:16px;flex-shrink:0;color:var(--c-ai)}.lead-card{display:grid;gap:var(--sp-3,12px)}.lead-card .row{gap:var(--sp-2,8px);align-items:center}.lead-icon{width:20px;height:20px;color:var(--c-primary)}.leave{display:block;margin:var(--sp-4,16px) auto 0}</style>
