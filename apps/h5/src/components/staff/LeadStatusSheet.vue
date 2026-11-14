<script setup lang="ts">
import type { LeadData } from '@/api/generated'
import { showToast } from 'vant'
import { shallowRef, watch } from 'vue'
import { updateLead } from '@/api/generated'
import { useMutation } from '@/composables/useMutation'
import { leadStatuses } from '@/utils/format'
const props = defineProps<{ lead: LeadData }>();
const emit = defineEmits<{ saved: [] }>()
const show = defineModel<boolean>({ default: false })
const status = shallowRef<LeadData['status']>(props.lead.status); const remark = shallowRef(props.lead.remark)
watch(() => show.value, value => { if (value) { status.value = props.lead.status; remark.value = props.lead.remark } })
const { saving, failure, run } = useMutation()
async function save() { const result = await run(() => updateLead({ path: { id: props.lead.id }, body: { status: status.value, remark: remark.value } })); if (result) { show.value = false; showToast('已保存'); emit('saved') } }
</script>
<template><van-popup v-model:show="show" position="bottom" round closeable role="dialog" aria-label="线索状态"><section class="sheet stack"><h2>线索状态</h2><van-radio-group v-model="status" aria-label="线索状态选项"><van-cell v-for="option in leadStatuses" :key="option.value" :title="option.label" clickable @click="status = option.value as LeadData['status']"><template #right-icon><van-radio :name="option.value" :aria-label="option.label" /></template></van-cell></van-radio-group><van-field v-model="remark" label="备注" type="textarea" maxlength="4000" /><p v-if="failure" class="error" role="alert">{{ failure }}</p><van-button type="primary" block :loading="saving" @click="save">保存</van-button></section></van-popup></template>
