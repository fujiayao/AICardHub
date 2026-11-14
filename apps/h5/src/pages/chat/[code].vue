<!-- 原型: A2 AI 对话 / A3 留资成功 -->
<script setup lang="ts">
import type { ChatMessage } from '@/composables/useChatStream'
import { showToast } from 'vant'
import { computed, shallowRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError, errorMessage } from '@/api/client'
import { createSession, feedback, messages as getMessages, publicCard } from '@/api/generated'
import AnonymousPortrait from '@/components/common/AnonymousPortrait.vue'
import ChatComposer from '@/components/common/ChatComposer.vue'
import ChatConversation from '@/components/common/ChatConversation.vue'
import DemoBadge from '@/components/common/DemoBadge.vue'
import ResourceState from '@/components/common/ResourceState.vue'
import DisabledCard from '@/components/visitor/DisabledCard.vue'
import LeadSheet from '@/components/visitor/LeadSheet.vue'
import LeadSuccess from '@/components/visitor/LeadSuccess.vue'
import { useChatStream } from '@/composables/useChatStream'
import { useResource } from '@/composables/useResource'
import { callPhone } from '@/platform'
import { useVisitorStore } from '@/stores/visitor'
import { sceneCampaign, sceneKey, sceneQuery, sceneSource } from '@/utils/scene'
const route = useRoute('/chat/[code]'); const router = useRouter(); const code = String(route.params.code)
const campaignId = sceneCampaign(route.query.e); const source = sceneSource(route.query.s)
const visitId = shallowRef<number>();
const visitor = useVisitorStore(); const sessionId = shallowRef<number>()
const lead = shallowRef(route.query.lead === '1')
const summary = shallowRef<{ name: string, phone: string, company_name: string }>()
const stream = useChatStream(() => `/api/v1/public/chat/sessions/${sessionId.value}/messages`)
const { messages, sending, error: chatError, model, leadPrompts } = stream
const { data, loading, error, reload } = useResource(async () => {
 const card = await publicCard({ path: { code }, query: { e: campaignId } })
 if (card.status === 'disabled') return { card, opening: '', questions: [] }
 await visitor.ensure()
 const key = `shuke.chat.${code}.${campaignId || 'business'}.${source}`
 const storedVisit = Number(sessionStorage.getItem(sceneKey(code, campaignId, source)))
 visitId.value = Number.isSafeInteger(storedVisit) && storedVisit > 0 ? storedVisit : undefined
 const remembered = Number(sessionStorage.getItem(key))
 if (remembered) {
  try { const history = await getMessages({ path: { id: remembered } }); messages.value = history.items; sessionId.value = remembered }
  catch (e) { if (!(e instanceof ApiError) || ![403, 404].includes(e.status)) throw e; sessionStorage.removeItem(key) }
 }
 let opening = card.assistant?.opening || ''; let questions = card.assistant?.guide_questions || []
 if (!sessionId.value) { const session = await createSession({ body: { card_code: code, campaign_id: campaignId, visit_id: visitId.value, source } }); sessionId.value = session.session_id; opening = session.opening; questions = session.guide_questions; sessionStorage.setItem(key, String(sessionId.value)) }
 if (typeof route.query.q === 'string') { const question = route.query.q; await router.replace({ path: route.path, query: sceneQuery(source, campaignId) }); void stream.send(question) }
 return { card, opening, questions }
})
const role = computed(() => data.value ? [data.value.card.title, data.value.card.dept].filter(Boolean).join('｜') : '')
async function down(message: ChatMessage) {
 if (message.id < 0 || message.feedback) return
 try { await feedback({ path: { id: message.id }, body: { feedback: 'down' } }); message.feedback = true; showToast('感谢反馈') } catch (e) { showToast(errorMessage(e)) }
}
</script>
<template><ResourceState :loading="loading" :error="error" @retry="reload"><DisabledCard v-if="data?.card.status === 'disabled'" :company="data.card.company" /><LeadSuccess v-else-if="summary && data" :name="data.card.name || ''" :phone="data.card.mobile" :summary="summary" :code="code" :back-query="sceneQuery(source, campaignId)" @continue="summary = undefined" /><main v-else-if="data" class="page chat-page"><header class="chat-nav"><button class="nav-back" aria-label="返回名片" @click="router.push({ path: `/card/${code}`, query: sceneQuery(source, campaignId) })"><span class="icon i-lucide-chevron-left" /></button><div class="chat-head"><span class="avatar avatar-ai"><img v-if="data.card.photo_url" :src="data.card.photo_url" :alt="`${data.card.name}的职业照`"><AnonymousPortrait v-else /></span><div class="chat-head-text"><b>{{ data.card.name }}的 AI 分身</b><span>内容由 AI 生成，仅供参考</span></div></div><button v-if="data.card.mobile" class="nav-phone" aria-label="拨打电话" @click="callPhone(data.card.mobile)"><span class="icon i-lucide-phone" /></button><span v-else class="nav-phone-spacer" /></header><div class="content"><DemoBadge :model="model" /><section v-if="!messages.length" class="welcome-wrap"><div class="welcome"><span class="welcome-avatar avatar avatar-ai"><img v-if="data.card.photo_url" :src="data.card.photo_url" :alt="`${data.card.name}的职业照`"><AnonymousPortrait v-else /></span><h2>你好，我是{{ data.card.name }}的 AI 分身</h2><p v-if="role" class="welcome-role">{{ role }}</p></div><div v-if="data.opening" class="welcome-opening"><article class="message assistant"><div class="bubble"><span class="ai-label">AI 分身</span><p class="preline opening-text">{{ data.opening }}</p></div></article></div><div v-if="data.questions.length" class="guide-list"><p class="guide-lbl">你可以这样问我</p><button v-for="question in data.questions" :key="question" class="guide-q" :disabled="sending" @click="stream.send(question)"><span class="icon i-lucide-sparkles guide-spark" /><span class="guide-q-text">{{ question }}</span><span class="icon i-lucide-chevron-right guide-arrow" /></button></div></section><ChatConversation :messages="messages" :sending="sending" @feedback="down" @retry="stream.retry" /><p v-if="chatError" class="error" role="alert">{{ chatError }}</p><section v-for="(prompt, index) in leadPrompts" :key="index" class="lead-card"><b>{{ prompt.title }}</b><p>{{ prompt.reason }}</p><div class="lead-card-row"><van-button type="primary" size="small" @click="lead = true">留下联系方式</van-button><van-button v-if="data.card.mobile" plain size="small" @click="callPhone(data.card.mobile)"><span class="icon i-lucide-phone" />直接打电话</van-button></div></section><button class="text-button leave" @click="lead = true">留下联系方式</button></div><ChatComposer :disabled="!sessionId" :sending="sending" @send="stream.send" @stop="stream.stop" /><LeadSheet v-model="lead" :code="code" :session-id="sessionId" :campaign-id="campaignId" :visit-id="visitId" :source="source" @submitted="summary = $event" /></main></ResourceState></template>
<style scoped>.chat-page{padding-bottom:140px;background:linear-gradient(180deg,var(--c-chat-bg-top) 0%,var(--c-bg) 260px)}.chat-nav{height:48px;display:grid;grid-template-columns:48px 1fr 48px;align-items:center;background:transparent;position:relative;z-index:3}.nav-back,.nav-phone{display:grid;place-items:center;border:0;padding:0;background:transparent;color:var(--c-ink);cursor:pointer}.nav-back .icon{width:24px;height:24px}.nav-phone .icon{width:22px;height:22px}.nav-phone-spacer{display:block}.chat-head{display:flex;align-items:center;gap:8px;justify-content:center;min-width:0}.chat-head .avatar{width:30px;height:30px;border-radius:var(--r-pill);overflow:hidden;flex:none;background:linear-gradient(165deg,var(--c-hero-top),var(--c-ink));position:relative}.chat-head .avatar img{width:100%;height:100%;object-fit:cover;object-position:center top}.avatar-ai::after{content:"";position:absolute;right:0;bottom:0;width:28%;height:28%;border-radius:var(--r-pill);background:var(--c-ai);border:2px solid var(--c-surface)}.chat-head-text{min-width:0}.chat-head-text b{display:block;font-size:var(--fs-base);color:var(--c-ink);line-height:1.3}.chat-head-text span{display:block;font-size:11px;color:var(--c-text-3);line-height:1.3}.content{padding:0}.welcome-wrap{display:grid;gap:4px}.welcome{display:flex;flex-direction:column;align-items:center;text-align:center;padding:24px 24px 8px}.welcome-avatar{position:relative;display:block;width:76px;height:76px;border-radius:var(--r-pill);overflow:hidden;background:linear-gradient(165deg,var(--c-hero-top),var(--c-ink));box-shadow:var(--sh-welcome)}.welcome-avatar img{width:100%;height:100%;object-fit:cover;object-position:center top}.welcome h2{margin:14px 0 4px;font-size:var(--fs-lg);color:var(--c-ink)}.welcome-role{margin:0;font-size:var(--fs-sm);color:var(--c-text-2)}.welcome-opening{padding:0 16px}.welcome-opening .message{max-width:88%}.welcome-opening .bubble{padding:var(--sp-3) var(--sp-4);background:var(--c-surface);border-radius:2px var(--r-lg) var(--r-lg);box-shadow:var(--sh-soft)}.welcome-opening .ai-label{display:block;color:var(--c-ai);font-size:var(--fs-xs);font-weight:600;margin-bottom:var(--sp-2)}.opening-text{margin:0}.guide-list{margin:4px 16px 0;display:flex;flex-direction:column;gap:8px}.guide-lbl{font-size:var(--fs-xs);color:var(--c-text-3);margin:6px 2px 0}.guide-q{display:flex;align-items:center;gap:10px;padding:12px 14px;border:0;border-radius:12px;background:var(--c-surface);font-size:var(--fs-base);color:var(--c-ink);box-shadow:var(--sh-soft);text-align:left;min-height:44px;cursor:pointer;width:100%}.guide-q:disabled{opacity:.5}.guide-spark{width:18px;height:18px;flex:none;color:var(--c-ai)}.guide-q-text{flex:1;min-width:0}.guide-arrow{width:16px;height:16px;flex:none;color:var(--c-text-3)}.lead-card{margin:0 16px 0 44px;padding:14px;border-radius:14px;background:var(--c-surface);border:1px solid var(--c-lead-card-line);box-shadow:var(--sh-soft)}.lead-card b{display:block;color:var(--c-ink);font-size:var(--fs-base)}.lead-card p{margin:4px 0 12px;font-size:var(--fs-sm);color:var(--c-text-2)}.lead-card-row{display:flex;gap:8px}.lead-card-row :deep(.van-button){flex:1}.lead-card-row .icon{width:16px;height:16px;margin-right:4px}.leave{display:block;margin:var(--sp-4,16px) auto 0}</style>
