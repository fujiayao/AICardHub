<!-- 原型: A2 AI 对话（暗色，复用 DarkCardHero + DarkInlineChat）/ A3 留资成功 / A4 停用 -->
<!-- 对话页：复用首页同一场景访问（ensureVisit 单飞，不重复 createVisit）；首次发送才建会话；返回名片仅带 s/e。 -->
<script setup lang="ts">
import { computed, onUnmounted, shallowRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { publicCard, updateVisit } from '@/api/generated'
import ResourceState from '@/components/common/ResourceState.vue'
import DarkCardHero from '@/components/visitor/DarkCardHero.vue'
import DarkInlineChat from '@/components/visitor/DarkInlineChat.vue'
import DisabledCard from '@/components/visitor/DisabledCard.vue'
import { useResource } from '@/composables/useResource'
import { ensureVisit } from '@/composables/useVisit'
import { callPhone, copyText, isWechat, saveContact, share } from '@/platform'
import { useVisitorStore } from '@/stores/visitor'
import { sceneCampaign, sceneQuery, sceneSource } from '@/utils/scene'
import '@/components/visitor/dark-card.css'

const route = useRoute('/chat/[code]'); const router = useRouter(); const visitor = useVisitorStore()
const code = computed(() => String(route.params.code))
const origin = window.location.origin
const eventId = computed(() => sceneCampaign(route.query.e))
const activeSource = computed(() => sceneSource(route.query.s))
const autoQuestion = computed(() => (typeof route.query.q === 'string' ? route.query.q : undefined))
const leadDeepLink = computed(() => route.query.lead === '1')
const wechat = shallowRef(false); const guide = shallowRef(false); const trackingError = shallowRef('')
const liveVisitId = shallowRef<number>(); let visitRevision = 0; let started = Date.now()

const { data: card, loading, error, reload } = useResource(async () => {
  return await publicCard({ path: { code: code.value }, query: { e: eventId.value } })
})

watch(card, (value) => {
  if (!value) return
  document.title = value.status === 'disabled' ? '该名片已停用' : `${value.name}｜${value.title}｜${value.company.short_name || value.company.name}`
  if (value.status === 'active') void trackVisit()
})

async function trackVisit() {
  // 优先复用首页/同场景已建访问（ensureVisit 读缓存 + 单飞）；直连对话无缓存时创建一次。
  const revision = ++visitRevision
  const activeCode = code.value; const campaign = eventId.value; const source = activeSource.value
  try {
    const id = await ensureVisit(() => visitor.ensure(), activeCode, campaign, source)
    if (revision !== visitRevision) return
    liveVisitId.value = id
  } catch (e) { trackingError.value = e instanceof Error && e.message ? `访问记录暂未同步：${e.message}` : '访问记录暂未同步，对话不受影响' }
}
function stay() {
  visitRevision++
  if (liveVisitId.value) {
    const id = liveVisitId.value; liveVisitId.value = undefined
    void updateVisit({ path: { id }, body: { stay_seconds: Math.min(86400, Math.floor((Date.now() - started) / 1000)) } }).catch((e) => { trackingError.value = e instanceof Error && e.message ? `停留记录未同步：${e.message}` : '停留记录未同步' })
  }
}
window.addEventListener('pagehide', stay)
onUnmounted(() => { stay(); window.removeEventListener('pagehide', stay) })

// code/campaign/source 变化才重载名片与访问；仅 q 变化不重载（DarkInlineChat 自行 watch 消费）。
watch([code, eventId, activeSource], () => { stay(); started = Date.now(); trackingError.value = ''; wechat.value = false; guide.value = false; void reload() })

// 对话页会话 key 固定 card/campaign/source，q 不进 key，避免仅移除 q 时 remount。
const sceneId = computed(() => `${code.value}.${eventId.value || 'business'}.${activeSource.value}`)

function back() { void router.push({ path: `/card/${code.value}`, query: sceneQuery(activeSource.value, eventId.value) }) }
// 只剥离 q，保留 s/e 与 lead（不触发 remount，也不重复打开留资弹层）。
function stripQuestion() {
  const query = { ...sceneQuery(activeSource.value, eventId.value), ...(leadDeepLink.value ? { lead: '1' } : {}) }
  void router.replace({ path: route.path, query })
}
function contact() { if (isWechat) guide.value = true; else saveContact(code.value) }
function onShare() {
  if (!card.value) return
  const query = `s=${activeSource.value}${eventId.value ? `&e=${eventId.value}` : ''}`
  share(`${card.value.name}｜${card.value.title}`, `${origin}/c/${card.value.code}?${query}`)
}
</script>

<template>
  <ResourceState :loading="loading" :error="error" @retry="reload">
    <DisabledCard v-if="card?.status === 'disabled'" :company="card.company" />
    <main v-else-if="card" class="vc-dark">
      <nav class="dk-nav">
        <button class="dk-nav-back" aria-label="返回名片" @click="back"><span class="icon i-lucide-chevron-left" />返回名片</button>
      </nav>
      <DarkCardHero
        :card="card"
        :has-wechat="Boolean(card.wechat_qr_url)"
        @contact="contact"
        @call="card.mobile && callPhone(card.mobile)"
        @wechat="wechat = true"
        @share="onShare"
      />
      <DarkInlineChat
        :key="sceneId"
        :card="card"
        :code="code"
        :campaign-id="eventId"
        :source="activeSource"
        :visit-id="liveVisitId"
        :auto-question="autoQuestion"
        :lead-deep-link="leadDeepLink"
        @auto-consumed="stripQuestion"
      />
      <p v-if="trackingError" class="vc-dark-note">{{ trackingError }}</p>

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
            <div class="wg-alt-row"><b class="num">{{ card.mobile }}</b><van-button size="small" @click="copyText(card.mobile)">复制</van-button></div>
          </div>
          <div class="wg-ok"><van-button plain @click="guide = false">知道了</van-button></div>
        </section>
      </van-overlay>
    </main>
  </ResourceState>
</template>

<style scoped>
.dk-nav { display: flex; align-items: center; height: 44px; padding: 0 10px; }
.dk-nav-back { display: flex; align-items: center; gap: 2px; border: 0; background: transparent; color: var(--dk-tag); font-size: 13px; cursor: pointer; }
.dk-nav-back .icon { width: 22px; height: 22px; }
.vc-dark-note { text-align: center; font-size: 10.5px; color: var(--dk-expo); padding: 8px 22px 14px; }
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
