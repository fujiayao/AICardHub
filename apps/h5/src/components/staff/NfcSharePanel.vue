<script setup lang="ts">
import { computed, watch } from 'vue'
import { cardShareLink } from '@/api/generated'
import NfcInstallHelp from '@/components/common/NfcInstallHelp.vue'
import ResourceState from '@/components/common/ResourceState.vue'
import { useResource } from '@/composables/useResource'
import { copyText, isAndroid, isIOS, isWechat, openAppLink } from '@/platform'
import { nfcHelperUrl } from '@/utils/nfc-link'

const props = defineProps<{ campaign?: number }>()
const emit = defineEmits<{ fallback: [tab: 'qr' | 'link'] }>()

const { data, loading, error, reload } = useResource(async () => {
  const [sticker, phone] = await Promise.all([
    cardShareLink({ query: { s: 'nfc' } }),
    props.campaign ? cardShareLink({ query: { s: 'nfc', e: props.campaign } }) : undefined,
  ])
  return { sticker: sticker.short_url, phone: (phone || sticker).short_url }
})
watch(() => props.campaign, () => { void reload() })

const emulateUrl = computed(() => data.value && nfcHelperUrl(data.value.phone, 'emulate', props.campaign))
const writeUrl = computed(() => data.value && nfcHelperUrl(data.value.sticker, 'write'))
function open(url: string | undefined) { if (url) openAppLink(url) }
</script>

<template>
  <ResourceState :loading="loading" :error="error" @retry="reload">
    <div v-if="data" class="nfc stack">
      <template v-if="isIOS">
        <div class="ai-hint row"><span class="icon i-lucide-smartphone-nfc" aria-hidden="true" /><span class="grow">当前 iPhone 可读取他人的 NFC 名片；发送自己的名片请使用二维码或系统分享。</span></div>
        <div class="ops">
          <van-button type="primary" block @click="emit('fallback', 'qr')"><span class="icon i-lucide-qr-code" aria-hidden="true" />展示二维码</van-button>
          <van-button block @click="emit('fallback', 'link')"><span class="icon i-lucide-share-2" aria-hidden="true" />系统分享</van-button>
        </div>
        <p class="muted small">读取他人名片时，将 iPhone 顶部靠近对方手机或贴纸，出现系统提示后点按打开；能否读取取决于机型与系统设置。</p>
      </template>
      <template v-else>
        <p v-if="isWechat" class="notice">微信内无法打开 NFC 助手：请点右上角「…」选择在浏览器打开，或复制下方链接、改用二维码。</p>
        <p v-else-if="!isAndroid" class="notice">手机 NFC 分享需要安卓手机上的 NFC 助手。请在安卓手机浏览器中打开本页，或改用二维码。</p>
        <section class="block stack">
          <div class="row between"><h3>手机碰一碰</h3><span class="tag">{{ campaign ? '展会活动' : '商务' }}</span></div>
          <p class="muted">在助手中预览并确认后开始模拟。对方手机靠近后按其系统提示打开链接；读取效果因机型、NFC 开关与锁屏状态而异。</p>
          <van-button type="primary" block :disabled="!emulateUrl || isWechat || !isAndroid" @click="open(emulateUrl)"><span class="icon i-lucide-nfc" aria-hidden="true" />打开 NFC 助手</van-button>
        </section>
        <section class="block stack">
          <h3>写入 NFC 贴纸</h3>
          <p class="muted">长期贴纸只写入固定名片链接，不带活动参数；写入后助手会回读校验。</p>
          <van-button block :disabled="!writeUrl || isWechat || !isAndroid" @click="open(writeUrl)"><span class="icon i-lucide-pen-line" aria-hidden="true" />写入 NFC 贴纸</van-button>
        </section>
        <p v-if="!emulateUrl" class="error">服务配置的名片地址不是公司自有 HTTPS 域名，无法唤起 NFC 助手；下方链接仍可复制，但正式使用前需管理员配置 HTTPS 域名。</p>
        <NfcInstallHelp />
        <section class="block stack">
          <h3>手动配置</h3>
          <p class="muted small">助手未自动打开时，复制完整 NFC 链接粘贴到助手中。此链接仅用于 NFC 配置，对外发送请使用「链接」页。</p>
          <p class="preline link num">{{ data.phone }}</p>
          <div class="ops">
            <van-button size="small" block @click="copyText(data.phone)">复制 NFC 链接</van-button>
            <van-button v-if="campaign" size="small" block @click="copyText(data.sticker)">复制贴纸链接</van-button>
            <van-button v-else size="small" block @click="emit('fallback', 'qr')">改用二维码</van-button>
          </div>
        </section>
        <p class="muted small">首次使用先安装安卓助手。若点击后未打开，请使用系统浏览器重试，或复制名片链接粘贴到助手。NFC 开关与手机支持情况会在助手中检查。</p>
      </template>
    </div>
  </ResourceState>
</template>

<style scoped>
.nfc{text-align:left}
.nfc .icon{width:18px;height:18px;margin-right:6px}
.ai-hint .icon{margin-right:0}
.block{padding:var(--sp-4);background:var(--c-bg);border-radius:var(--r-md);gap:var(--sp-2)}
.block h3{font-size:var(--fs-base);color:var(--c-ink)}
.ops{display:grid;grid-template-columns:1fr 1fr;gap:var(--sp-2)}
.link{padding:var(--sp-3);background:var(--c-surface);border-radius:var(--r-sm);font-size:var(--fs-xs)}
</style>
