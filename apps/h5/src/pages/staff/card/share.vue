<!-- 原型: B4 发送名片 -->
<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue'
import { useRoute } from 'vue-router'
import { campaigns, card as getCard } from '@/api/generated'
import PageShell from '@/components/common/PageShell.vue'
import ResourceState from '@/components/common/ResourceState.vue'
import NfcSharePanel from '@/components/staff/NfcSharePanel.vue'
import ShareLinkPanel from '@/components/staff/ShareLinkPanel.vue'
import ShareMediaPanel from '@/components/staff/ShareMediaPanel.vue'
import { useResource } from '@/composables/useResource'
import { openMiniCardShare, useMiniProgram } from '@/platform/mini-program'

type Tab = 'qr' | 'poster' | 'link' | 'nfc'
const tabs: Tab[] = ['qr', 'poster', 'link', 'nfc']
const route = useRoute()
const tab = shallowRef<Tab>(tabs.includes(route.query.tab as Tab) ? route.query.tab as Tab : 'qr')
const inMiniProgram = useMiniProgram()
watch(inMiniProgram, (active) => { if (active && tab.value === 'nfc') tab.value = 'qr' }, { immediate: true })
const scene = shallowRef<'business' | 'exhibition'>('business'); const selectedEvent = shallowRef<number>()
const { data, loading, error, reload } = useResource(async () => { const [card, events] = await Promise.all([getCard(), campaigns()]); return { card, events } })
const campaign = computed(() => scene.value === 'exhibition' ? selectedEvent.value : undefined)
const ready = computed(() => scene.value === 'business' || Boolean(selectedEvent.value))
const role = computed(() => data.value ? [data.value.card.display_title || data.value.card.title, data.value.card.company_name].filter(Boolean).join('｜') : '')
</script>

<template>
  <PageShell title="发送名片" back>
    <ResourceState :loading="loading" :error="error" @retry="reload">
      <template v-if="data">
        <van-tabs v-model:active="tab"><van-tab title="二维码" name="qr" /><van-tab title="海报" name="poster" /><van-tab title="链接" name="link" /><van-tab v-if="!inMiniProgram" title="手机 NFC" name="nfc" /></van-tabs>
        <section class="scene panel">
          <div class="row between scene-head"><span class="scene-title">分享场景</span><span class="tag">{{ scene === 'business' ? '商务交流' : '展会获客' }}</span></div>
          <div class="scene-opts">
            <button type="button" class="scene-opt" :class="{ active: scene === 'business' }" @click="scene = 'business'">商务</button>
            <button type="button" class="scene-opt" :class="{ active: scene === 'exhibition' }" @click="scene = 'exhibition'">展会</button>
          </div>
          <template v-if="scene === 'exhibition'">
            <label for="share-event">选择有效活动</label>
            <select id="share-event" v-model="selectedEvent" class="event-select"><option :value="undefined">请选择活动</option><option v-for="event in data.events" :key="event.id" :value="event.id">{{ event.name }}</option></select>
            <p v-if="!data.events.length" class="muted small">暂无进行中的活动，请联系管理员创建并启用。</p>
            <p v-else class="muted small">选择活动后生成专属链接、二维码和海报，访问与留资将计入该活动。</p>
          </template>
          <p v-else class="muted small">用于商务拜访和日常线上对接，不归入展会活动。</p>
        </section>
        <section v-if="ready" class="panel share-panel stack">
          <van-button v-if="inMiniProgram && data.card.status === 'active'" type="primary" block @click="openMiniCardShare(data.card.code, campaign, true)">转发小程序名片</van-button>
          <NfcSharePanel v-if="tab === 'nfc' && !inMiniProgram" :campaign="campaign" @fallback="tab = $event" />
          <ShareLinkPanel v-else-if="tab === 'link'" :title="`${data.card.name}｜${data.card.display_title}`" :campaign="campaign">
            <div class="share-id"><h2>{{ data.card.name }}</h2><p class="muted role">{{ role }}</p></div>
          </ShareLinkPanel>
          <ShareMediaPanel v-else-if="tab === 'qr' || tab === 'poster'" :key="tab" :kind="tab" :campaign="campaign">
            <div class="share-id"><h2>{{ data.card.name }}</h2><p class="muted role">{{ role }}</p></div>
            <p class="muted hint">扫码查看名片，和我的 AI 分身聊聊</p>
          </ShareMediaPanel>
        </section>
      </template>
    </ResourceState>
  </PageShell>
</template>

<style scoped>
.event-select{width:100%;min-height:44px;border:1px solid var(--c-line);border-radius:var(--r-md);padding:8px;background:var(--c-surface);color:var(--c-text)}
.scene{padding:var(--sp-4)}
.scene-head{align-items:center;margin-bottom:var(--sp-3)}
.scene-title{font-size:var(--fs-sm);color:var(--c-text)}
.scene-opts{display:flex;gap:var(--sp-2);margin-bottom:var(--sp-2)}
.scene-opt{flex:1;min-height:40px;border:1px solid var(--c-line);border-radius:var(--r-md);background:var(--c-surface);color:var(--c-text-3);font-size:var(--fs-sm)}
.scene-opt.active{border-color:var(--c-primary-line);background:var(--c-primary-soft);color:var(--c-primary)}
.share-panel{text-align:center;padding:var(--sp-6) var(--sp-5)}
.share-id h2{font-size:var(--fs-lg)}
.share-id .role{margin-top:4px;font-size:var(--fs-sm)}
.hint{font-size:var(--fs-sm)}
</style>
