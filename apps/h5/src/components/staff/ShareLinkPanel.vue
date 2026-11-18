<script setup lang="ts">
import { computed, watch } from 'vue'
import { cardShareLink } from '@/api/generated'
import ResourceState from '@/components/common/ResourceState.vue'
import { useResource } from '@/composables/useResource'
import { copyText, share } from '@/platform'
import { previewShareUrl } from '@/utils/card-share'

const props = defineProps<{ title: string, campaign?: number }>()
const { data, loading, error, reload } = useResource(() => cardShareLink({ query: { s: 'link', e: props.campaign } }))
watch(() => props.campaign, () => { void reload() })
const url = computed(() => data.value ? previewShareUrl(data.value.short_url, window.location.origin) : '')
</script>

<template>
  <ResourceState :loading="loading" :error="error" @retry="reload">
    <slot />
    <p class="preline link">{{ url }}</p>
    <van-button type="primary" block @click="copyText(url)"><span class="icon i-lucide-copy" aria-hidden="true" />复制链接</van-button>
    <van-button block @click="share(title, url)"><span class="icon i-lucide-share-2" aria-hidden="true" />系统分享</van-button>
  </ResourceState>
</template>

<style scoped>
.link{padding:var(--sp-4);background:var(--c-bg);border-radius:var(--r-md);text-align:left;font-size:var(--fs-sm)}
.icon{width:18px;height:18px;margin-right:6px}
</style>
