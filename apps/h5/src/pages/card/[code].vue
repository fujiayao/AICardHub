<!-- 原型: A1 名片首页（暗色真实商务名片：身份 → 联系方式/简介/公司/主营业务 → AI 入口）/ A4 停用 / A5 微信引导 -->
<!-- 首页绝不内联聊天、绝不建会话；AI 入口/引导问题/问问 AI 跳 /chat（带 q 发送一次）。 -->
<script setup lang="ts">
import { computed, onUnmounted, shallowRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { publicCard, updateVisit } from '@/api/generated'
import ResourceState from '@/components/common/ResourceState.vue'
import DarkCardBody from '@/components/visitor/DarkCardBody.vue'
import DarkCardHero from '@/components/visitor/DarkCardHero.vue'
import DisabledCard from '@/components/visitor/DisabledCard.vue'
import { useResource } from '@/composables/useResource'
import { ensureVisit } from '@/composables/useVisit'
import { callPhone, copyText, isWechat, saveContact, share } from '@/platform'
import { useVisitorStore } from '@/stores/visitor'
import { cardShareUrl } from '@/utils/app-path'
import { sceneCampaign, sceneQuery, sceneSource } from '@/utils/scene'
import '@/components/visitor/dark-card.css'

const route = useRoute('/card/[code]'); const router = useRouter(); const visitor = useVisitorStore()
const code = computed(() => String(route.params.code))
const origin = window.location.origin
const eventId = computed(() => sceneCampaign(route.query.e))
const activeSource = computed(() => sceneSource(route.query.s))
const guide = shallowRef(false); const wechat = shallowRef(false); const trackingError = shallowRef('')
const liveVisitId = shallowRef<number>(); let visitRevision = 0; let started = Date.now()

const { data: card, loading, error, reload } = useResource(async () => {
  return await publicCard({ path: { code: code.value }, query: { e: eventId.value } })
})

// 旧链接兼容：/card?q= 或 /card?lead=1 → /chat（保留 s/e/q/lead），在上报访问之前跳转，避免首页+对话重复访问。
const legacyQuestion = computed(() => (typeof route.query.q === 'string' && route.query.q.trim() ? route.query.q : undefined))
const legacyLead = computed(() => route.query.lead === '1')
let redirecting = false
function redirectLegacy(): boolean {
  if (redirecting || (!legacyQuestion.value && !legacyLead.value)) return redirecting
  redirecting = true
  const query = { ...sceneQuery(activeSource.value, eventId.value), ...(legacyQuestion.value ? { q: legacyQuestion.value } : {}), ...(legacyLead.value ? { lead: '1' } : {}) }
  void router.replace({ path: `/chat/${code.value}`, query })
  return true
}

watch(card, (value) => {
  if (!value) return
  document.title = value.status === 'disabled' ? '该名片已停用' : `${value.name}｜${value.title}｜${value.company.short_name || value.company.name}`
  // 停用名片绝不跳对话、不上报，只显示公司信息。
  if (value.status !== 'active') return
  if (redirectLegacy()) return
  void trackVisit()
})
// 同一首页组件内仅 q/lead 变化时，名片已为 active 才跳转；停用不跳。
watch([legacyQuestion, legacyLead], () => { if (card.value?.status === 'active') redirectLegacy() })

async function trackVisit() {
  // 场景键在 await 前快照，revision guard 防止快速切换把旧来源写进新场景。
  const revision = ++visitRevision
  const activeCode = code.value; const campaign = eventId.value; const source = activeSource.value
  try {
    // 首页每次进入/刷新/返回都新建访问；对话页复用该进行中请求或缓存。
    const id = await ensureVisit(() => visitor.ensure(), activeCode, campaign, source, { forceNew: true })
    if (revision !== visitRevision) return
    liveVisitId.value = id
  } catch (e) { trackingError.value = e instanceof Error && e.message ? `访问记录暂未同步：${e.message}` : '访问记录暂未同步，浏览名片不受影响' }
}
function stay() {
  visitRevision++
  if (liveVisitId.value) {
    const id = liveVisitId.value; liveVisitId.value = undefined
    void updateVisit({ path: { id }, body: { stay_seconds: Math.min(86400, Math.floor((Date.now() - started) / 1000)) } }).catch(() => { trackingError.value = '停留记录未同步' })
  }
}
window.addEventListener('pagehide', stay)
onUnmounted(() => { stay(); window.removeEventListener('pagehide', stay) })

watch([code, eventId, activeSource], () => { stay(); started = Date.now(); trackingError.value = ''; guide.value = false; wechat.value = false; void reload() })

function openChat(question?: string) {
  void router.push({ path: `/chat/${code.value}`, query: { ...sceneQuery(activeSource.value, eventId.value), ...(question ? { q: question } : {}) } })
}
function openLead() {
  void router.push({ path: `/chat/${code.value}`, query: { ...sceneQuery(activeSource.value, eventId.value), lead: '1' } })
}
function contact() { if (isWechat) guide.value = true; else saveContact(code.value) }
function onShare() {
  if (!card.value) return
  // 分享永远走短链 /c/{code}，仅带来源+活动，绝不带 q/lead。
  const query = `s=${activeSource.value}${eventId.value ? `&e=${eventId.value}` : ''}`
  share(`${card.value.name}｜${card.value.title}`, cardShareUrl(card.value.code, query, origin))
}
</script>

<template>
  <ResourceState :loading="loading" :error="error" @retry="reload">
    <DisabledCard v-if="card?.status === 'disabled'" :company="card.company" />
    <main v-else-if="card" class="vc-dark">
      <DarkCardHero
        :card="card"
        :has-wechat="Boolean(card.wechat_qr_url)"
        @contact="contact"
        @call="card.mobile && callPhone(card.mobile)"
        @wechat="wechat = true"
        @share="onShare"
      />
      <DarkCardBody :card="card" @ask="openChat" @open-chat="openChat()" @open-lead="openLead" />
      <p v-if="trackingError" class="vc-dark-note">{{ trackingError }}</p>

      <div class="dk-bar">
        <button v-if="card.mobile" class="dk-bar-mini" @click="callPhone(card.mobile)"><span class="icon i-lucide-phone" />电话</button>
        <button v-if="card.wechat_qr_url" class="dk-bar-mini" @click="wechat = true"><span class="icon i-lucide-message-circle" />微信</button>
        <button class="dk-bar-primary" @click="openChat()"><span class="icon i-lucide-message-square" />和TA聊聊</button>
      </div>

      <van-popup v-model:show="wechat" position="bottom" round closeable>
        <div class="sheet stack">
          <h2>添加微信</h2>
          <img v-if="card.wechat_qr_url" :src="card.wechat_qr_url" alt="员工微信二维码">
          <p class="muted">长按识别二维码添加微信</p>
        </div>
      </van-popup>

      <van-overlay :z-index="30" :show="guide" @click="guide = false">
        <section class="wechat-guide" role="dialog" aria-label="在浏览器打开" @click.stop>
          <span class="icon i-lucide-arrow-up-right wg-arrow" aria-hidden="true" />
          <h2>在浏览器中打开，即可存入通讯录</h2>
          <p class="wg-lead">微信里无法直接保存联系人。点击右上角 <span class="wg-dots" aria-hidden="true"><i /><i /><i /></span>，选择「在浏览器打开」，再点“存通讯录”。</p>
          <div v-if="card.mobile" class="wg-alt">
            <span class="wg-alt-lbl">也可以直接复制号码</span>
            <div class="wg-alt-row"><b class="num">{{ card.mobile }}</b><van-button size="small" class="wg-copy" @click="copyText(card.mobile)">复制</van-button></div>
          </div>
          <div class="wg-ok"><van-button plain class="wg-ok-btn" @click="guide = false">知道了</van-button></div>
        </section>
      </van-overlay>
    </main>
  </ResourceState>
</template>

<style scoped>
.vc-dark-note { text-align: center; font-size: 10.5px; color: var(--dk-expo); padding: 8px 22px 14px; }
.dk-bar { position: fixed; left: 0; right: 0; bottom: 0; z-index: 20; max-width: 480px; margin-inline: auto; display: flex; align-items: center; gap: 10px; padding: 10px 16px calc(10px + env(safe-area-inset-bottom)); background: linear-gradient(180deg, var(--dk-composer-0), var(--dk-composer-1) 36%); }
.dk-bar-mini { display: flex; flex-direction: column; align-items: center; gap: 3px; border: 0; background: transparent; font-size: 10px; color: var(--dk-act-label); cursor: pointer; flex: none; }
.dk-bar-mini .icon { width: 20px; height: 20px; color: var(--dk-mint); }
.dk-bar-primary { flex: 1; display: flex; align-items: center; justify-content: center; gap: 7px; height: 46px; border: 0; border-radius: 14px; background: linear-gradient(140deg, var(--dk-mint), var(--dk-mint-deep)); color: var(--dk-on-mint); font-size: 15px; font-weight: 700; cursor: pointer; }
.dk-bar-primary .icon { width: 18px; height: 18px; }
.wechat-guide { padding: 60px 28px; display: block; color: var(--dk-txt); }
.wechat-guide h2 { color: var(--dk-txt); font-size: 18px; margin-top: 8px; }
.wg-arrow { display: block; margin-left: auto; width: 48px; height: 48px; color: var(--dk-txt); }
.wg-lead { margin-top: 12px; font-size: 13px; line-height: 1.8; color: var(--dk-tag); }
.wg-dots { display: inline-flex; align-items: center; gap: 3px; padding: 2px 8px; border-radius: 20px; background: var(--dk-surface-soft); vertical-align: middle; }
.wg-dots i { width: 4px; height: 4px; border-radius: 20px; background: var(--dk-txt); }
.wg-alt { margin-top: 28px; padding: 16px; border-radius: 12px; background: var(--dk-surface-soft); }
.wg-alt-lbl { font-size: 13px; color: var(--dk-tag); }
.wg-alt-row { display: flex; align-items: center; justify-content: space-between; margin-top: 8px; }
.wg-alt-row .num { font-size: 20px; letter-spacing: .04em; color: var(--dk-txt); }
.wg-ok { text-align: center; margin-top: 36px; }
.sheet.stack { padding: 20px; display: grid; gap: 12px; justify-items: center; }
.sheet.stack img { max-width: 220px; }
</style>
