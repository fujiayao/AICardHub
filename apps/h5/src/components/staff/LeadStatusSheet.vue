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
<template><van-popup v-model:show="show" position="bottom" round closeable role="dialog" aria-label="线索状态"><section class="sheet stack"><header class="sheet-head"><span class="icon i-lucide-flag head-icon" aria-hidden="true" /><h2>标记线索状态</h2></header><van-radio-group v-model="status" aria-label="线索状态选项"><van-cell-group inset><van-cell v-for="option in leadStatuses" :key="option.value" :title="option.label" clickable @click="status = option.value as LeadData['status']"><template #right-icon><van-radio :name="option.value" :aria-label="option.label" /></template></van-cell></van-cell-group></van-radio-group><div class="field-group"><p class="group-label">跟进备注</p><van-cell-group inset><van-field v-model="remark" type="textarea" rows="3" autosize maxlength="4000" show-word-limit placeholder="记录沟通要点、下一步计划" aria-label="跟进备注" /></van-cell-group></div><p v-if="failure" class="error" role="alert">{{ failure }}</p><div class="actions"><van-button type="primary" block :loading="saving" @click="save">保存</van-button></div></section></van-popup></template>
<style scoped>
.sheet-head{display:flex;align-items:center;gap:var(--sp-2)}
.head-icon{color:var(--c-text-2)}
.group-label{font-size:var(--fs-sm);color:var(--c-text-2);padding:0 var(--sp-4) var(--sp-1)}
.actions{margin-top:var(--sp-2)}
</style>
