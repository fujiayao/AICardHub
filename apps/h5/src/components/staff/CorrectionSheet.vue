<script setup lang="ts">
import { showToast } from 'vant'
import { reactive, watch } from 'vue'
import { createCorrection } from '@/api/generated'
import { useMutation } from '@/composables/useMutation'
const props = defineProps<{ question?: string, wrongAnswer?: string, messageId?: number, source?: 'test' | 'visitor_chat' | 'manual' }>()
const emit = defineEmits<{ saved: [] }>()
const show = defineModel<boolean>({ default: false })
const form = reactive({ question: '', correct_answer: '' })
watch(() => show.value, value => { if (value) { form.question = props.question || ''; form.correct_answer = '' } })
const { saving, failure, run } = useMutation()
async function save() { const result = await run(() => createCorrection({ body: { ...form, wrong_answer: props.wrongAnswer || '', message_id: props.messageId, source: props.source || 'manual' } })); if (result) { show.value = false; showToast('已保存纠错'); emit('saved') } }
</script>
<template><van-popup v-model:show="show" position="bottom" round closeable role="dialog" aria-label="纠错回答"><section class="sheet stack"><header class="sheet-head"><span class="icon i-lucide-pencil-line head-icon" aria-hidden="true" /><h2>纠错回答</h2></header><van-form @submit="save"><van-cell-group inset><van-field v-model="form.question" label="问题" type="textarea" rows="2" autosize :readonly="!!question" placeholder="访客可能会这样问" :rules="[{ required: true, message: '请填写问题' }]" /></van-cell-group><details v-if="wrongAnswer" class="wrong"><summary class="muted small">原回答</summary><p class="preline muted">{{ wrongAnswer }}</p></details><van-cell-group inset><van-field v-model="form.correct_answer" label="正确答案" type="textarea" rows="4" autosize placeholder="填写希望 AI 给出的答案" :rules="[{ required: true, message: '请填写正确答案' }]" /></van-cell-group><p class="muted small help">保存为个人纠错，公开使用仍须管理员批准。</p><p v-if="failure" class="error" role="alert">{{ failure }}</p><div class="actions"><van-button block type="primary" native-type="submit" :loading="saving">保存纠错</van-button></div></van-form></section></van-popup></template>
<style scoped>
.sheet-head{display:flex;align-items:center;gap:var(--sp-2)}
.head-icon{color:var(--c-ai)}
.wrong{padding:0 var(--sp-1)}
.help{padding:0 var(--sp-1)}
.actions{margin-top:var(--sp-2)}
</style>
