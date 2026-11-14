<script setup lang="ts">
import { reactive, shallowRef } from 'vue'
import { createLead } from '@/api/generated'
import { useMutation } from '@/composables/useMutation'
const props = defineProps<{ code: string, sessionId?: number }>()
const emit = defineEmits<{ submitted: [summary: { name: string, phone: string, company_name: string }] }>()
const show = defineModel<boolean>({ default: false })
const form = reactive({ name: '', phone: '', company_name: '', need: '' })
const consent = shallowRef(false)
const { saving, failure, run } = useMutation()
async function submit() {
 if (!consent.value) return
 const result = await run(() => createLead({ body: { ...form, card_code: props.code, session_id: props.sessionId, consent: true } }))
 if (result) { show.value = false; emit('submitted', { name: form.name, phone: form.phone, company_name: form.company_name }) }
}
</script>
<template><van-popup v-model:show="show" position="bottom" round closeable role="dialog" aria-label="留下联系方式"><section class="sheet"><h2>留下联系方式</h2><p class="muted">仅在您同意后提交，用于工作人员联系与需求跟进。</p><van-form @submit="submit"><van-field v-model="form.name" label="姓名" placeholder="怎么称呼您" maxlength="80" :rules="[{ required: true, message: '请填写姓名' }]" /><van-field v-model="form.phone" label="联系电话" type="tel" placeholder="请输入手机号" maxlength="11" :rules="[{ pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' }]" /><van-field v-model="form.company_name" label="公司名称" placeholder="选填" maxlength="150" /><van-field v-model="form.need" label="需求描述" type="textarea" placeholder="您希望进一步了解什么" maxlength="100" show-word-limit /><van-checkbox v-model="consent" shape="square" aria-label="隐私同意" class="consent">我已阅读并同意将以上信息用于联系和需求跟进</van-checkbox><p v-if="failure" role="alert" class="error">{{ failure }}</p><van-button block type="primary" native-type="submit" :disabled="!consent" :loading="saving">提交</van-button></van-form></section></van-popup></template>
<style scoped>.consent{margin:20px 0;font-size:var(--fs-sm)}</style>
