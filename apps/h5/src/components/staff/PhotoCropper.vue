<script setup lang="ts">
import { onUnmounted, shallowRef, useTemplateRef } from 'vue'
const props = defineProps<{ file: File }>()
const emit = defineEmits<{ cropped: [file: File], cancel: [] }>()
const url = URL.createObjectURL(props.file)
const zoom = shallowRef(1); const x = shallowRef(0); const y = shallowRef(0)
const image = useTemplateRef<HTMLImageElement>('image')
let start: { x: number, y: number } | undefined
function move(event: PointerEvent) { if (!start) return; x.value = Math.max(-100, Math.min(100, event.clientX - start.x)); y.value = Math.max(-140, Math.min(140, event.clientY - start.y)) }
function down(event: PointerEvent) { start = { x: event.clientX - x.value, y: event.clientY - y.value }; (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId) }
function crop() {
 const img = image.value; if (!img) return
 const canvas = document.createElement('canvas'); canvas.width = 750; canvas.height = 1000
 const context = canvas.getContext('2d'); if (!context) return
 const base = Math.max(240 / img.naturalWidth, 320 / img.naturalHeight)
 const width = img.naturalWidth * base * zoom.value; const height = img.naturalHeight * base * zoom.value
 context.drawImage(img, ((240 - width) / 2 + x.value) * 750 / 240, ((320 - height) / 2 + y.value) * 1000 / 320, width * 750 / 240, height * 1000 / 320)
 canvas.toBlob(blob => { if (blob) emit('cropped', new File([blob], 'portrait.jpg', { type: 'image/jpeg' })) }, 'image/jpeg', .9)
}
onUnmounted(() => URL.revokeObjectURL(url))
</script>
<template><div class="sheet stack"><h2>裁剪职业照</h2><p class="muted">固定 3:4，拖动照片并调整缩放</p><div class="crop-frame" @pointerdown="down" @pointermove="move" @pointerup="start = undefined" @pointercancel="start = undefined"><img ref="image" :src="url" alt="职业照裁剪预览" :style="{ transform: `translate(${x}px, ${y}px) scale(${zoom})` }"></div><label for="photo-zoom">缩放</label><input id="photo-zoom" v-model="zoom" type="range" min="1" max="3" step="0.05"><van-button type="primary" @click="crop">完成裁剪</van-button><van-button @click="$emit('cancel')">取消</van-button></div></template>
<style scoped>.crop-frame{width:240px;height:320px;overflow:hidden;margin:auto;background:var(--c-ink);touch-action:none;display:flex;align-items:center;justify-content:center}.crop-frame img{min-width:100%;min-height:100%;object-fit:cover;max-width:none;pointer-events:none}</style>
