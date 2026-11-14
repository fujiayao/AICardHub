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
<template><PageShell title="发送名片" back><ResourceState :loading="loading" :error="error" @retry="reload"><template v-if="data"><van-tabs v-model:active="tab"><van-tab title="二维码" name="qr" /><van-tab title="海报" name="poster" /><van-tab title="链接" name="link" /></van-tabs><section class="scene panel"><div class="row between scene-head"><span class="scene-title">分享场景</span><span class="pending">待接口支持</span></div><div class="scene-opts"><button class="scene-opt active" type="button" disabled>商务</button><button class="scene-opt" type="button" disabled>展会</button></div><p class="muted small">当前默认商务场景；展会活动归因需后台开通后启用，暂不可切换。</p></section><section class="panel share-panel stack"><div class="share-id"><h2>{{ data.card.name }}</h2><p class="muted">{{ data.card.display_title || data.card.title }}</p></div><template v-if="tab !== 'link'"><div class="media"><img v-if="tab === 'qr' ? data.share.qr_url : data.share.poster_url" :src="tab === 'qr' ? data.share.qr_url : data.share.poster_url" :alt="tab === 'qr' ? '名片二维码' : '名片海报'" @click="preview = true"><van-empty v-else description="分享图片尚未生成" /></div><p class="muted hint">扫码和我的 AI 分身聊聊</p><van-button type="primary" block @click="preview = true"><span class="icon i-lucide-download" aria-hidden="true" />{{ tab === 'qr' ? '保存图片' : '保存海报' }}</van-button><p class="muted small">打开大图后长按保存到相册</p></template><template v-else><p class="preline link">{{ sourceUrl(data.share.short_url) }}</p><van-button type="primary" block @click="copyText(sourceUrl(data.share.short_url))"><span class="icon i-lucide-copy" aria-hidden="true" />复制链接</van-button><van-button block @click="share(`${data.card.name}｜${data.card.display_title}`, sourceUrl(data.share.short_url))"><span class="icon i-lucide-share-2" aria-hidden="true" />系统分享</van-button></template></section><van-popup v-model:show="preview" round closeable><div class="sheet stack"><img :src="tab === 'qr' ? data.share.qr_url : data.share.poster_url" alt="长按保存分享图片"><p>长按图片保存</p></div></van-popup></template></ResourceState></PageShell></template>
<style scoped>
.scene{padding:var(--sp-4)}
.scene-head{align-items:center;margin-bottom:var(--sp-3)}
.scene-title{font-size:var(--fs-sm);color:var(--c-text)}
.pending{font-size:var(--fs-xs);color:var(--c-text-3);background:var(--c-bg);padding:2px 8px;border-radius:var(--r-sm)}
.scene-opts{display:flex;gap:var(--sp-2);margin-bottom:var(--sp-2)}
.scene-opt{flex:1;min-height:40px;border:1px solid var(--c-line);border-radius:var(--r-md);background:var(--c-surface);color:var(--c-text-3);font-size:var(--fs-sm)}
.scene-opt.active{border-color:var(--c-primary-line);background:var(--c-primary-soft);color:var(--c-primary)}
.scene-opt:disabled{opacity:.7}
.share-panel{text-align:center;padding:var(--sp-6) var(--sp-5)}
.share-id h2{font-size:var(--fs-lg)}
.media{display:grid;place-items:center;padding:var(--sp-4);background:var(--c-bg);border-radius:var(--r-lg)}
.media img{width:100%;max-width:280px;max-height:420px;object-fit:contain;border-radius:var(--r-md)}
.hint{font-size:var(--fs-sm)}
.share-panel .icon{margin-right:6px}
.link{padding:var(--sp-4);background:var(--c-bg);border-radius:var(--r-md);overflow-wrap:anywhere;text-align:left;font-size:var(--fs-sm)}
</style>
