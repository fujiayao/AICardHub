<script setup lang="ts">
import { showToast } from 'vant'
import { computed, shallowRef, watch } from 'vue'
import { polish } from '@/api/generated'
import { useMutation } from '@/composables/useMutation'
const props = defineProps<{ title: string, field: 'persona_extra' | 'opening', value: string, saving?: boolean }>()
const emit = defineEmits<{ save: [text: string] }>()
const text = shallowRef(props.value); const candidate = shallowRef<string>(); const show = shallowRef(false)
const limit = computed(() => props.field === 'persona_extra' ? 300 : 2000)
watch(() => props.value, value => { text.value = value })
const { saving: polishing, failure, run } = useMutation()
async function generate() { const result = await run(() => polish({ body: { text: text.value, field: props.field } })); if (result) { candidate.value = result.text; show.value = true } }
function replace() { if (candidate.value) { text.value = candidate.value.slice(0, limit.value); showToast('已替换候选，请保存生效'); show.value = false } }
</script>
<template><section class="panel stack"><header class="editor-head row between"><h2>{{ title }}</h2><span class="count small">{{ text.length }}/{{ limit }}</span></header><van-cell-group inset><van-field v-model="text" :aria-label="title" type="textarea" rows="4" autosize :maxlength="limit" :placeholder="`填写${title}`" /></van-cell-group><p v-if="failure" class="error" role="alert">{{ failure }}</p><div class="actions"><van-button plain :disabled="!text.trim()" :loading="polishing" @click="generate"><span class="icon i-lucide-wand-sparkles" aria-hidden="true" />润色</van-button><van-button type="primary" :loading="saving" @click="emit('save', text)">保存</van-button></div><van-popup v-model:show="show" position="bottom" round closeable><section class="sheet stack"><header class="sheet-head"><span class="icon i-lucide-sparkles head-icon" aria-hidden="true" /><h2>润色候选</h2></header><van-cell-group inset><div class="candidate preline">{{ candidate }}</div></van-cell-group><div class="actions"><van-button type="primary" block @click="replace">替换</van-button><van-button block @click="show = false">取消</van-button></div></section></van-popup></section></template>
<style scoped>
.editor-head{align-items:baseline}
.count{color:var(--c-text-3)}
.actions{display:flex;gap:var(--sp-2)}
.actions .van-button{flex:1}
.actions .icon{margin-right:6px}
.sheet-head{display:flex;align-items:center;gap:var(--sp-2)}
.head-icon{color:var(--c-ai)}
.candidate{padding:var(--sp-3) var(--sp-4);color:var(--c-text)}
</style>
