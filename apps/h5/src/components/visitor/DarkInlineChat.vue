<script setup lang="ts">
// 原型: 名片原型-demo.html AI 区（置顶头 / 内联消息 / 留资 / 置顶输入 + 横向 chips）。
// 懒加载：静态名片立即可见；挂载后先 visitor.ensure 再恢复历史；首次提问/留资才创建会话，不为浏览产生空会话。
import type { PublicCard } from '@/api/generated'
import type { Source } from '@/utils/scene'
import { onMounted, onScopeDispose, shallowRef } from 'vue'
import { ApiError } from '@/api/client'
import { createSession, messages as getMessages } from '@/api/generated'
import DarkMessages from '@/components/visitor/DarkMessages.vue'
import LeadSheet from '@/components/visitor/LeadSheet.vue'
import { useChatStream } from '@/composables/useChatStream'
import { callPhone } from '@/platform'
import { useVisitorStore } from '@/stores/visitor'
import { sceneKey } from '@/utils/scene'

const props = defineProps<{
  card: PublicCard
  code: string
  campaignId?: number
  source: Source
  visitId?: number
  autoQuestion?: string
  leadDeepLink?: boolean
}>()
const emit = defineEmits<{ leadSubmitted: [summary: { name: string, phone: string, company_name: string }], autoConsumed: [] }>()

const visitor = useVisitorStore()
const sessionId = shallowRef<number>()
const stream = useChatStream(() => `/api/v1/public/chat/sessions/${sessionId.value}/messages`)
const { messages, sending, error, leadPrompts } = stream
const opening = shallowRef(props.card.assistant?.opening || '')
const questions = shallowRef<string[]>(props.card.assistant?.guide_questions || [])
const restoring = shallowRef(true)
const initError = shallowRef('')
const lead = shallowRef(false)
const leadDone = shallowRef<{ name: string } | undefined>()
const draft = shallowRef('')
const composing = shallowRef(false)

let disposed = false
let sessionPending: Promise<number | undefined> | undefined
const storageKey = `shuke.chat.${props.code}.${props.campaignId || 'business'}.${props.source}`

onMounted(restore)
onScopeDispose(() => { disposed = true; stream.stop() })

async function restore() {
  try {
    await visitor.ensure()
    if (disposed) return
    const remembered = Number(sessionStorage.getItem(storageKey))
    if (remembered) {
      try {
        const history = await getMessages({ path: { id: remembered } })
        if (disposed) return
        messages.value = history.items; sessionId.value = remembered
      } catch (e) {
        if (!(e instanceof ApiError) || ![403, 404].includes(e.status)) throw e
        sessionStorage.removeItem(storageKey)
      }
    }
  } catch (e) {
    initError.value = e instanceof ApiError ? e.message : '对话暂不可用，请稍后重试'
  } finally {
    if (!disposed) restoring.value = false
  }
  if (!disposed && !initError.value && props.leadDeepLink) await openLead()
  if (!disposed && !initError.value && props.autoQuestion) { emit('autoConsumed'); void send(props.autoQuestion) }
}

// 单飞 + 失败可重试；仅首次提问时创建会话
function ensureSession(): Promise<number | undefined> {
  if (sessionId.value) return Promise.resolve(sessionId.value)
  if (sessionPending) return sessionPending
  sessionPending = (async () => {
    await visitor.ensure()
    if (disposed) return undefined
    const stored = Number(sessionStorage.getItem(sceneKey(props.code, props.campaignId, props.source)))
    const visit = props.visitId ?? (Number.isSafeInteger(stored) && stored > 0 ? stored : undefined)
    const session = await createSession({ body: { card_code: props.code, campaign_id: props.campaignId, visit_id: visit, source: props.source } })
    if (disposed) return undefined
    sessionId.value = session.session_id; opening.value = session.opening; questions.value = session.guide_questions
    sessionStorage.setItem(storageKey, String(session.session_id))
    return session.session_id
  })().catch((e) => { initError.value = e instanceof ApiError ? e.message : '对话初始化失败，请重试'; return undefined })
    .finally(() => { sessionPending = undefined })
  return sessionPending
}

async function send(question?: string) {
  if (composing.value) return
  const text = (question ?? draft.value).trim()
  if (!text || sending.value || restoring.value || sessionPending) return
  initError.value = ''
  const id = await ensureSession()
  if (!id || disposed) return
  draft.value = ''
  void stream.send(text)
}
function onEnter(e: KeyboardEvent) { if (e.isComposing || composing.value) return; e.preventDefault(); void send() }
async function openLead() {
  try { await visitor.ensure(); if (!disposed) lead.value = true }
  catch (e) { if (!disposed) initError.value = e instanceof ApiError ? e.message : '暂时无法打开留资表单，请重试' }
}
function onLead(summary: { name: string, phone: string, company_name: string }) {
  leadDone.value = { name: summary.name }; leadPrompts.value = []; emit('leadSubmitted', summary)
}
</script>

<template>
  <section class="dk-ai-section">
    <div class="dk-ai-head">
      <span class="dk-ai-mark"><span class="icon i-lucide-sparkles" /></span>
      <div class="dk-ai-head-text">
        <div class="dk-ai-t">{{ card.name ? `${card.name}的 AI 助手` : 'AI 助手' }}</div>
        <div class="dk-ai-s">基于已公开资料回答 · 不确定会直说</div>
      </div>
      <div class="dk-ai-badge"><span class="dk-ai-badge-dot" />AI 可用</div>
    </div>

    <div v-if="opening" class="dk-assistant-row">
      <span class="dk-assistant-who">AI</span>
      <div class="dk-assistant-bubble"><p class="dk-assistant-text">{{ opening }}</p></div>
    </div>

    <DarkMessages :messages="messages" :sending="sending" @retry="stream.retry" />
    <p v-if="error" class="dk-error" role="alert">{{ error }}</p>
    <p v-if="initError" class="dk-error" role="alert">{{ initError }}</p>

    <section v-if="leadDone" class="dk-lead dk-lead-ok">
      <div class="dk-ok"><span class="icon i-lucide-check" />已提交{{ leadDone.name ? ` · ${leadDone.name}` : '' }}，工作人员会尽快与您联系</div>
    </section>

    <section v-for="(prompt, index) in leadPrompts" :key="index" class="dk-lead">
      <h4>{{ prompt.title }}</h4>
      <p>{{ prompt.reason }}</p>
      <div class="dk-lead-row">
        <button class="dk-lead-primary" @click="openLead">留下联系方式</button>
        <button v-if="card.mobile" class="dk-lead-plain" @click="callPhone(card.mobile!)">直接打电话</button>
      </div>
    </section>

    <button v-if="!leadDone" class="dk-lead-link" @click="openLead">主动留下联系方式</button>

    <div class="dk-composer">
      <div v-if="questions.length" class="dk-chips">
        <button v-for="question in questions" :key="question" class="dk-chip" :disabled="sending || restoring" @click="send(question)">{{ question }}</button>
      </div>
      <div class="dk-inputbar">
        <input
          v-model="draft" type="text" aria-label="输入消息"
          :placeholder="restoring ? '正在接入…' : '问点什么，比如「做过哪些项目」'"
          :disabled="restoring" autocomplete="off"
          @keydown.enter="onEnter" @compositionstart="composing = true" @compositionend="composing = false"
        >
        <button class="dk-send" :disabled="sending || restoring || !draft.trim()" aria-label="发送" @click="send()">
          <span class="icon i-lucide-arrow-up" />
        </button>
      </div>
      <p class="dk-disclaimer">内容由 AI 生成，仅供参考 · 关键信息请与业务人员确认</p>
    </div>

    <LeadSheet v-model="lead" :code="code" :session-id="sessionId" :campaign-id="campaignId" :visit-id="visitId" :source="source" @submitted="onLead" />
  </section>
</template>

<style scoped>
.dk-ai-section {
  display: flex; flex-direction: column; flex: 1 0 auto; padding: 0 0 8px;
  border-top: 1px solid var(--dk-line);
  background: linear-gradient(180deg, var(--dk-ai-bg-0), var(--dk-ai-bg-1));
}
.dk-ai-head {
  display: flex; align-items: center; gap: 10px; padding: 18px 22px 14px;
  position: sticky; top: 0; z-index: 12;
  background: var(--dk-head-bg); backdrop-filter: blur(10px); border-bottom: 1px solid var(--dk-line);
}
.dk-ai-mark {
  width: 32px; height: 32px; border-radius: 10px; flex: none;
  background: linear-gradient(145deg, var(--dk-mark-0), var(--dk-mark-1));
  border: 1px solid var(--dk-avatar-ring); display: grid; place-items: center;
}
.dk-ai-mark .icon { width: 16px; height: 16px; color: var(--dk-mint); }
.dk-ai-head-text { min-width: 0; flex: 1; }
.dk-ai-t { font-size: 13.5px; font-weight: 600; letter-spacing: .01em; color: var(--dk-txt); }
.dk-ai-s { font-size: 10.5px; color: var(--dk-expo); margin-top: 2px; }
.dk-ai-badge { display: flex; align-items: center; gap: 5px; font-size: 10px; color: var(--dk-mint); flex: none; }
.dk-ai-badge-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--dk-mint); }

.dk-assistant-row { display: flex; gap: 8px; padding: 16px 22px 0; }
.dk-assistant-who {
  width: 24px; height: 24px; border-radius: 7px; flex: none; margin-top: 2px; display: grid; place-items: center;
  font-size: 10px; font-weight: 700; background: var(--dk-mint-dim); color: var(--dk-mint); border: 1px solid var(--dk-avatar-ring);
}
.dk-assistant-bubble {
  font-size: 13.5px; line-height: 1.78; padding: 11px 14px; border-radius: 14px; max-width: calc(100% - 40px);
  background: var(--dk-surface-2); border: 1px solid var(--dk-line); border-top-left-radius: 5px; color: var(--dk-bubble-ai);
}
.dk-assistant-text { margin: 0; white-space: pre-wrap; word-break: break-word; }

.dk-error { margin: 8px 22px 0; font-size: 12px; color: var(--dk-blue); }

.dk-lead {
  margin: 8px 22px 0; padding: 16px; border-radius: 14px;
  background: linear-gradient(150deg, var(--dk-lead-0), var(--dk-lead-1)); border: 1px solid var(--dk-mint-line);
}
.dk-lead h4 { font-size: 12.5px; font-weight: 650; margin-bottom: 3px; color: var(--dk-lead-title); }
.dk-lead p { font-size: 11px; color: var(--dk-cite-strong); margin-bottom: 11px; line-height: 1.6; }
.dk-lead-row { display: flex; gap: 8px; }
.dk-lead-primary { flex: 1; padding: 9px; border: 0; border-radius: 9px; background: var(--dk-mint); color: var(--dk-on-mint); font-size: 12.5px; font-weight: 700; cursor: pointer; }
.dk-lead-plain { flex: 1; padding: 9px; border: 1px solid var(--dk-mint-line); border-radius: 9px; background: transparent; color: var(--dk-mint); font-size: 12.5px; cursor: pointer; }
.dk-lead-ok .dk-ok { display: flex; align-items: center; gap: 7px; font-size: 12px; color: var(--dk-mint); }
.dk-lead-ok .dk-ok .icon { width: 16px; height: 16px; }
.dk-lead-link { align-self: center; margin: 14px 0 2px; border: 0; background: transparent; color: var(--dk-mint); font-size: 12px; cursor: pointer; letter-spacing: .02em; text-decoration: underline; text-underline-offset: 3px; }

.dk-composer {
  position: sticky; bottom: 0; z-index: 14; padding: 10px 18px calc(18px + env(safe-area-inset-bottom));
  background: linear-gradient(180deg, var(--dk-composer-0), var(--dk-composer-1) 28%);
}
.dk-chips { display: flex; gap: 7px; overflow-x: auto; padding: 2px 4px 10px; scrollbar-width: none; }
.dk-chips::-webkit-scrollbar { display: none; }
.dk-chip {
  flex: none; font-size: 11.5px; padding: 7px 13px; border-radius: 20px; cursor: pointer;
  background: var(--dk-surface-soft); border: 1px solid var(--dk-line-strong); color: var(--dk-tag); white-space: nowrap; transition: .16s;
}
.dk-chip:disabled { opacity: .5; cursor: default; }
.dk-inputbar {
  display: flex; gap: 8px; align-items: center; background: var(--dk-surface);
  border: 1px solid var(--dk-line-strong); border-radius: 22px; padding: 5px 5px 5px 16px;
}
.dk-inputbar input { flex: 1; min-width: 0; background: none; border: none; outline: none; color: var(--dk-txt); font-size: 13px; font-family: inherit; padding: 7px 0; }
.dk-inputbar input::placeholder { color: var(--dk-placeholder); }
.dk-send { width: 33px; height: 33px; border-radius: 50%; border: 0; cursor: pointer; flex: none; background: var(--dk-mint); display: grid; place-items: center; transition: .16s; }
.dk-send:disabled { opacity: .45; cursor: default; }
.dk-send .icon { width: 16px; height: 16px; color: var(--dk-on-mint); }
.dk-disclaimer { text-align: center; font-size: 9.5px; color: var(--dk-disclaimer); margin-top: 9px; letter-spacing: .02em; }
</style>
