<script setup lang="ts">
import type { PublicCard } from '@/api/generated'
import { computed, shallowRef, watch } from 'vue'
import { copyText, prepareShareImage, share, shareImage } from '@/platform'
import { cardShareUrl } from '@/utils/app-path'
import { publicCardShare } from '@/utils/card-share'

const props = defineProps<{ card: PublicCard, query: string }>()
const open = defineModel<boolean>({ required: true })
const origin = window.location.origin
const data = computed(() => publicCardShare(props.card, props.query, origin))
const image = computed(() => {
  const url = new URL(cardShareUrl(props.card.code, props.query, origin))
  url.searchParams.set('image', '1')
  url.searchParams.set('s', 'poster')
  return url.href
})
const loading = shallowRef(true)
const failed = shallowRef(false)
const imageFile = shallowRef<File>()
const revision = shallowRef(0)
const imageSrc = computed(() => `${image.value}&v=${revision.value}`)
async function prepare() {
  const version = ++revision.value
  loading.value = true; failed.value = false; imageFile.value = undefined
  try {
    const file = await prepareShareImage(imageSrc.value)
    if (version === revision.value && open.value) imageFile.value = file
  }
  catch { /* The image element reports loading errors with a visible retry. */ }
}
watch([open, image], ([visible]) => {
  if (visible) void prepare()
  else { revision.value++; imageFile.value = undefined }
})
</script>

<template>
  <van-popup v-model:show="open" position="bottom" round closeable class="card-share-sheet">
    <section class="share-content" aria-labelledby="card-share-title">
      <h2 id="card-share-title">分享名片</h2>
      <p class="share-subtitle">把个人信息和合作方向，一起递给对方</p>
      <div v-if="open" class="share-preview" :aria-busy="loading">
        <van-loading v-if="loading && !failed" class="share-loading" size="24">正在生成商务名片</van-loading>
        <img v-if="!failed" :key="imageSrc" :src="imageSrc" :alt="`${card.name}的商务名片，包含姓名、职务、公司和访问二维码`" @load="loading = false" @error="failed = true; loading = false">
        <div v-else class="share-error" role="alert"><p>名片图片暂时无法加载</p><van-button size="small" @click="prepare">重新生成</van-button></div>
      </div>
      <p class="share-hint">长按图片保存后发送给微信好友；对方长按识别图中二维码，即可打开名片。</p>
      <van-button v-if="imageFile && !failed" block type="primary" @click="shareImage(imageFile)">发送名片图片</van-button>
      <div class="share-links">
        <van-button block @click="copyText(data.url)">复制名片链接</van-button>
        <van-button block @click="share(data.title, data.url, data.text)">分享链接</van-button>
      </div>
      <p class="share-note">链接在微信中的卡片外观由微信决定；图片保留完整名片配色和排版。</p>
    </section>
  </van-popup>
</template>

<style scoped>
.card-share-sheet { max-height: 94dvh; background: var(--c-surface); }
.share-content { padding: 24px 20px calc(24px + env(safe-area-inset-bottom)); display: grid; gap: 12px; }
.share-content h2 { font-size: var(--fs-lg); color: var(--c-ink); }
.share-subtitle, .share-hint { color: var(--c-text-2); font-size: var(--fs-sm); line-height: 1.6; }
.share-preview { position: relative; min-height: 180px; background: var(--c-bg); border-radius: var(--r-lg); overflow: hidden; }
.share-preview img { display: block; width: 100%; height: auto; }
.share-loading { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; gap: 8px; }
.share-error { min-height: 180px; display: grid; place-content: center; justify-items: center; gap: 12px; color: var(--c-text-2); }
.share-links { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.share-note { font-size: var(--fs-xs); line-height: 1.5; color: var(--c-text-3); }
</style>
