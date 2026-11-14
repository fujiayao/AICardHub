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
<template><section class="panel stack"><h2>{{ title }}</h2><van-field v-model="text" :aria-label="title" type="textarea" :maxlength="limit" show-word-limit :placeholder="`填写${title}`" /><p v-if="failure" class="error" role="alert">{{ failure }}</p><div class="row"><van-button plain :disabled="!text.trim()" :loading="polishing" @click="generate">润色</van-button><van-button plain :loading="saving" @click="emit('save', text)">保存{{ title }}</van-button></div><van-popup v-model:show="show" position="bottom" round closeable><section class="sheet stack"><h2>润色候选</h2><p class="preline">{{ candidate }}</p><van-button type="primary" @click="replace">替换</van-button><van-button @click="show = false">取消</van-button></section></van-popup></section></template>
