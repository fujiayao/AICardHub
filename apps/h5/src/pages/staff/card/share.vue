<!-- 原型: B4 发送名片 -->
<script setup lang="ts">
import { shallowRef } from 'vue'
import { cardShare, card as getCard } from '@/api/generated'
import PageShell from '@/components/common/PageShell.vue'
import ResourceState from '@/components/common/ResourceState.vue'
import { useResource } from '@/composables/useResource'
import { copyText, share } from '@/platform'
const tab = shallowRef('qr'); const preview = shallowRef(false)
const { data, loading, error, reload } = useResource(async () => { const [share, card] = await Promise.all([cardShare(), getCard()]); return { share, card } })
function sourceUrl(url: string) { const result = new URL(url, window.location.origin); result.searchParams.set('s', 'link'); return result.href }
</script>
<template><PageShell title="发送名片" back><ResourceState :loading="loading" :error="error" @retry="reload"><template v-if="data"><van-tabs v-model:active="tab"><van-tab title="二维码" name="qr" /><van-tab title="海报" name="poster" /><van-tab title="链接" name="link" /></van-tabs><section class="panel share-panel stack"><h2>{{ data.card.name }}</h2><p class="muted">{{ data.card.display_title || data.card.title }}</p><template v-if="tab !== 'link'"><img v-if="tab === 'qr' ? data.share.qr_url : data.share.poster_url" :src="tab === 'qr' ? data.share.qr_url : data.share.poster_url" :alt="tab === 'qr' ? '名片二维码' : '名片海报'" @click="preview = true"><van-empty v-else description="分享图片尚未生成" /><p class="muted">扫码和我的 AI 分身聊聊</p><van-button type="primary" @click="preview = true">{{ tab === 'qr' ? '保存图片' : '保存海报' }}</van-button><p class="muted small">打开大图后长按保存到相册</p></template><template v-else><p class="preline link">{{ sourceUrl(data.share.short_url) }}</p><van-button type="primary" @click="copyText(sourceUrl(data.share.short_url))">复制链接</van-button><van-button @click="share(`${data.card.name}｜${data.card.display_title}`, sourceUrl(data.share.short_url))">系统分享</van-button></template></section><van-popup v-model:show="preview" round closeable><div class="sheet stack"><img :src="tab === 'qr' ? data.share.qr_url : data.share.poster_url" alt="长按保存分享图片"><p>长按图片保存</p></div></van-popup></template></ResourceState></PageShell></template>
<style scoped>.share-panel{text-align:center;padding:32px 24px}.share-panel img{width:100%;max-height:460px;object-fit:contain}.link{padding:16px;background:var(--c-bg);border-radius:var(--r-md)}</style>
