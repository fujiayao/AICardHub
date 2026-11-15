<!-- 原型: B4 NFC 助手入口（未安装助手时的帮助与公开名片预览，不计访问） -->
<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { publicCard } from '@/api/generated'
import NfcInstallHelp from '@/components/common/NfcInstallHelp.vue'
import ResourceState from '@/components/common/ResourceState.vue'
import { useResource } from '@/composables/useResource'
import { isIOS } from '@/platform'
import { parseNfcQuery } from '@/utils/nfc-link'

const route = useRoute()
const parsed = computed(() => parseNfcQuery(route.query))
const invalid = computed(() => typeof parsed.value === 'string' ? parsed.value : '')
const params = computed(() => typeof parsed.value === 'string' ? undefined : parsed.value)
const mode = computed(() => params.value?.mode)
const campaign = computed(() => params.value?.campaign)
const { data, loading, error, reload } = useResource(async () => {
  const current = params.value
  return current ? await publicCard({ path: { code: current.code }, query: { e: current.campaign } }) : undefined
})
watch(() => JSON.stringify(route.query), () => { void reload() })
const role = computed(() => data.value ? [data.value.title, data.value.company.short_name || data.value.company.name].filter(Boolean).join('｜') : '')
</script>

<template>
  <main class="page">
    <van-nav-bar title="NFC 助手"><template #title><h1 class="nav-title">NFC 助手</h1></template></van-nav-bar>
    <div class="content">
      <section v-if="invalid" class="panel stack center" role="alert">
        <span class="icon i-lucide-link-2-off mark" aria-hidden="true" />
        <h2>链接无效</h2>
        <p class="muted">{{ invalid }}</p>
      </section>
      <ResourceState v-else :loading="loading" :error="error" @retry="reload">
        <template v-if="data">
          <section class="panel stack">
            <div class="row between"><h2>{{ mode === 'write' ? '写入 NFC 贴纸' : '手机碰一碰分享' }}</h2><span class="tag">{{ campaign ? '展会活动' : '商务' }}</span></div>
            <p class="muted">本页在未安装或未关联 NFC 助手时显示，用于确认名片内容。名片预览不会记录为客户访问。</p>
            <div class="preview">
              <b>{{ data.name || '未命名' }}</b>
              <span class="muted">{{ role }}</span>
              <span v-if="data.campaign" class="muted small">活动：{{ data.campaign.name }}</span>
              <span v-if="data.status === 'disabled'" class="error">该名片已停用，无法用于 NFC 分享。</span>
            </div>
          </section>
          <section v-if="isIOS" class="panel stack">
            <h2>iPhone 说明</h2>
            <p class="muted">iPhone 可读取他人的 NFC 名片；发送自己的名片请回到员工端使用二维码或系统分享。</p>
          </section>
          <section v-else class="panel stack">
            <h2>如何使用</h2>
            <ol class="steps muted">
              <li>在安卓手机上安装 NFC 助手。</li>
              <li>回到员工端「发送名片 → 手机 NFC」，再点按助手入口；或在助手中粘贴员工端复制的 NFC 链接。</li>
              <li>在助手中核对名片后，由你手动开始{{ mode === 'write' ? '写入并回读校验' : '模拟' }}。</li>
            </ol>
            <NfcInstallHelp />
            <p class="muted small">助手只关联公司自有 HTTPS 域名下的本页面，普通名片链接仍在浏览器中打开。</p>
          </section>
        </template>
      </ResourceState>
    </div>
  </main>
</template>

<style scoped>
.nav-title{font-size:var(--fs-md);font-weight:600}
.center{text-align:center;justify-items:center}
.mark{width:40px;height:40px;color:var(--c-text-3)}
.preview{display:grid;gap:4px;padding:var(--sp-4);background:var(--c-bg);border-radius:var(--r-md)}
.preview b{font-size:var(--fs-lg);color:var(--c-ink)}
.steps{padding-left:20px;display:grid;gap:6px;list-style:decimal}
</style>
