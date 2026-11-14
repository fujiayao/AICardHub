<!-- 原型: A1 公开名片 / A4 停用 / A5 微信引导 -->
<script setup lang="ts">
import { computed, onUnmounted, shallowRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createVisit, publicCard, updateVisit } from '@/api/generated'
import DemoBadge from '@/components/common/DemoBadge.vue'
import PhotoAvatar from '@/components/common/PhotoAvatar.vue'
import ResourceState from '@/components/common/ResourceState.vue'
import CardDetails from '@/components/visitor/CardDetails.vue'
import CardHero from '@/components/visitor/CardHero.vue'
import DisabledCard from '@/components/visitor/DisabledCard.vue'
import { useResource } from '@/composables/useResource'
import { callPhone, copyText, isWechat, openMap, saveContact } from '@/platform'
import { useVisitorStore } from '@/stores/visitor'
const route = useRoute('/card/[code]'); const router = useRouter(); const visitor = useVisitorStore()
const code = computed(() => String(route.params.code))
const origin = window.location.origin
const guide = shallowRef(false); const wechat = shallowRef(false); const trackingError = shallowRef('')
let visitId: number | undefined; let visitRevision = 0; let started = Date.now()
const { data: card, loading, error, reload } = useResource(async () => {
 const result = await publicCard({ path: { code: code.value } })
 return result
})
watch(card, value => { if (!value) return; document.title = value.status === 'disabled' ? '该名片已停用' : `${value.name}｜${value.title}｜数科`; if (value.status === 'active') void trackVisit() })
async function trackVisit() {
 const revision = ++visitRevision; const activeCode = code.value
 try { await visitor.ensure(); const source = ['nfc', 'qr', 'poster', 'link', 'sig'].includes(String(route.query.s)) ? String(route.query.s) as 'nfc' | 'qr' | 'poster' | 'link' | 'sig' : 'link'; const result = await createVisit({ body: { card_code: activeCode, source } }); if (revision === visitRevision) visitId = result.visit_id; else await updateVisit({ path: { id: result.visit_id }, body: { stay_seconds: Math.min(86400, Math.floor((Date.now() - started) / 1000)) } }) }
 catch { trackingError.value = '访问记录暂未同步，浏览名片不受影响' }
}
function stay() { visitRevision++; if (visitId) { const id = visitId; visitId = undefined; void updateVisit({ path: { id }, body: { stay_seconds: Math.min(86400, Math.floor((Date.now() - started) / 1000)) } }).catch(() => { trackingError.value = '停留记录未同步' }) } }
window.addEventListener('pagehide', stay)
onUnmounted(() => { stay(); window.removeEventListener('pagehide', stay) })
function chat(question?: string) { router.push({ path: `/chat/${code.value}`, query: question ? { q: question } : {} }) }
watch(code, () => { stay(); started = Date.now(); trackingError.value = ''; guide.value = false; void reload() })
function contact() { if (isWechat) guide.value = true; else saveContact(code.value) }
</script>
<template><ResourceState :loading="loading" :error="error" @retry="reload"><DisabledCard v-if="card?.status === 'disabled'" :company="card.company" /><main v-else-if="card" class="page"><CardHero :card="card" /><div class="content card-content"><section class="panel ai-card stack"><div class="row"><PhotoAvatar :src="card.photo_url" :name="card.name || ''" /><div class="grow"><h2>{{ card.name }}的 AI 分身</h2><span class="ai-tag tag">AI 可用</span></div><span class="icon i-lucide-sparkles ai-symbol" /></div><DemoBadge /><p class="ai-hint">{{ card.assistant?.opening || '欢迎与我的 AI 分身交流' }}</p><button v-for="question in card.assistant?.guide_questions" :key="question" class="question" @click="chat(question)">{{ question }}<span class="icon i-lucide-chevron-right" /></button></section><div class="quick-actions"><button :disabled="!card.mobile" @click="card.mobile && callPhone(card.mobile)"><span class="icon i-lucide-phone" />打电话</button><button @click="contact"><span class="icon i-lucide-contact-round" />存通讯录</button><button :disabled="!card.company.address" @click="card.company.address && openMap(card.company.address)"><span class="icon i-lucide-map-pin" />导航</button><button v-if="card.wechat_qr_url" @click="wechat = true"><span class="icon i-lucide-qr-code" />加微信</button><button v-else @click="copyText(`${origin}/c/${code}?s=link`)"><span class="icon i-lucide-link" />复制链接</button></div><CardDetails :card="card" @question="chat" /><p v-if="trackingError" class="muted small">{{ trackingError }}</p><footer class="muted small footer">内容由公司官方维护<br><button class="text-button" @click="router.push({ path: `/chat/${code}`, query: { lead: '1' } })">留下联系方式</button></footer></div><div class="bottom-bar"><button v-if="card.mobile" class="icon-button" aria-label="拨打电话" @click="callPhone(card.mobile)"><span class="icon i-lucide-phone" /></button><van-button type="primary" @click="chat()">和TA聊聊</van-button></div><van-popup v-model:show="wechat" position="bottom" round closeable><div class="sheet stack"><h2>添加微信</h2><img v-if="card.wechat_qr_url" :src="card.wechat_qr_url" alt="员工微信二维码"><p class="muted">长按识别二维码添加微信</p></div></van-popup><van-overlay :show="guide" @click="guide = false"><section class="wechat-guide" role="dialog" aria-label="在浏览器打开"><span class="icon i-lucide-arrow-up-right" /><h2>点击右上角 ···</h2><p>选择「在浏览器打开」，即可一键存入通讯录</p><p>也可以直接复制号码</p><van-button v-if="card.mobile" @click.stop="copyText(card.mobile)">复制 {{ card.mobile }}</van-button><van-button plain @click="guide = false">知道了</van-button></section></van-overlay></main></ResourceState></template>
<style scoped>.card-content{margin-top:-38px;position:relative}.ai-card{box-shadow:var(--sh-float)}.ai-symbol{color:var(--c-ai)}.question{display:flex;justify-content:space-between;align-items:center;text-align:left;min-height:44px;padding:10px 12px;border:1px solid var(--c-line);background:var(--c-surface);border-radius:var(--r-md);color:var(--c-ink)}.question .icon{width:16px}.quick-actions{display:grid;grid-template-columns:repeat(4,1fr);background:var(--c-surface);border-radius:var(--r-lg);padding:12px 0}.quick-actions button{display:grid;justify-items:center;gap:8px;border:0;background:transparent;min-height:60px;color:var(--c-ink);font-size:var(--fs-xs)}.quick-actions button:disabled{opacity:.4}.footer{text-align:center;padding:12px}.wechat-guide{padding:60px 28px;display:grid;gap:24px;color:var(--c-surface)}.wechat-guide h2{color:var(--c-surface)}.wechat-guide>.icon{justify-self:end;width:48px;height:48px}</style>
