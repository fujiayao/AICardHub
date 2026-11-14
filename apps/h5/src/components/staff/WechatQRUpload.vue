<script setup lang="ts">
import { showToast } from 'vant'
import { watch } from 'vue'
import { uploadWechatQR } from '@/api/generated'
import { useMutation } from '@/composables/useMutation'

defineProps<{ value: string, disabled?: boolean }>()
const emit = defineEmits<{ uploaded: [url: string], clear: [], busy: [value: boolean] }>()
const { saving, failure, run } = useMutation()
watch(saving, value => emit('busy', value), { flush: 'sync' })

async function choose(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024) {
    showToast('请选择 5MB 以内的 JPG、PNG 或 WebP 图片')
    return
  }
  const body = new FormData()
  body.append('file', file)
  const result = await run(() => uploadWechatQR({ body }))
  if (result) {
    emit('uploaded', result.wechat_qr_url)
    showToast('微信二维码已即时保存')
  }
}
</script>

<template>
  <section class="qr-upload stack" aria-labelledby="wechat-qr-heading">
    <h2 id="wechat-qr-heading">微信二维码</h2>
    <img v-if="value" :src="value" alt="微信二维码预览" class="qr-preview">
    <p v-else class="muted">尚未上传微信二维码，访客端将隐藏加微信入口。</p>
    <label for="wechat-qr-file">{{ value ? '更换微信二维码' : '上传微信二维码' }}</label>
    <input id="wechat-qr-file" type="file" accept="image/jpeg,image/png,image/webp" :disabled="disabled || saving" @change="choose">
    <p class="muted small">支持 5MB 以内 JPG、PNG、WebP；上传成功后即时保存。</p>
    <van-loading v-if="saving" size="20" role="status" aria-label="正在上传微信二维码">正在上传…</van-loading>
    <p v-if="failure" class="error" role="alert">{{ failure }}，可重新选择图片重试。</p>
    <button v-if="value" type="button" class="text-button danger-button" :disabled="disabled || saving" @click="emit('clear')">移除微信二维码（保存后生效）</button>
  </section>
</template>

<style scoped>
.qr-upload{padding:16px;background:var(--c-surface);border-radius:var(--r-lg)}
.qr-preview{width:180px;max-height:240px;object-fit:contain;margin:auto}
input{max-width:100%}
</style>
