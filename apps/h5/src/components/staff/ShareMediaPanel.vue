<script setup lang="ts">
import { shallowRef, watch } from 'vue'
import { cardShare } from '@/api/generated'
import ResourceState from '@/components/common/ResourceState.vue'
import { useResource } from '@/composables/useResource'

const props = defineProps<{ kind: 'qr' | 'poster', campaign?: number }>()
const preview = shallowRef(false)
const { data, loading, error, reload } = useResource(() => cardShare({ query: { s: 'link', e: props.campaign } }))
watch(() => props.campaign, () => { void reload() })
const image = () => (props.kind === 'qr' ? data.value?.qr_url : data.value?.poster_url) || ''
</script>

<template>
  <ResourceState :loading="loading" :error="error" @retry="reload">
    <div class="media">
      <img v-if="image()" :src="image()" :alt="kind === 'qr' ? '名片二维码' : '名片海报'" @click="preview = true">
      <van-empty v-else description="分享图片尚未生成" />
    </div>
    <slot />
    <van-button type="primary" block :disabled="!image()" @click="preview = true"><span class="icon i-lucide-download" aria-hidden="true" />{{ kind === 'qr' ? '保存图片' : '保存海报' }}</van-button>
    <p class="muted small">在微信内长按图片即可保存到相册</p>
    <van-popup v-model:show="preview" round closeable><div class="sheet stack"><img :src="image()" alt="长按保存分享图片"><p>长按图片保存</p></div></van-popup>
  </ResourceState>
</template>

<style scoped>
.media{display:grid;place-items:center;padding:var(--sp-4);background:var(--c-bg);border-radius:var(--r-lg)}
.media img{width:100%;max-width:280px;max-height:420px;object-fit:contain;border-radius:var(--r-md)}
.icon{width:18px;height:18px;margin-right:6px}
</style>
