<script setup lang="ts">
import { nfcApkUrl } from '@/utils/nfc-link'
const apk = nfcApkUrl()
</script>

<template>
  <section class="install stack">
    <h3>安装 NFC 助手</h3>
    <template v-if="apk">
      <p class="muted">仅限安卓手机。安装后返回本页，再点「在 NFC 助手中打开」。</p>
      <van-button block :href="apk" target="_blank" rel="noopener"><span class="icon i-lucide-download" aria-hidden="true" />下载安卓助手</van-button>
    </template>
    <p v-else class="muted">安卓助手正在调试，尚未公开发布。需要试用请联系管理员获取安装包。</p>
  </section>
</template>

<style scoped>
.install{padding:var(--sp-4);background:var(--c-bg);border-radius:var(--r-md);gap:var(--sp-2)}
.install h3{font-size:var(--fs-base);color:var(--c-ink)}
.install .icon{width:18px;height:18px;margin-right:6px}
</style>
