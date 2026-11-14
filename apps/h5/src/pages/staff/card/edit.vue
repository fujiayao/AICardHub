<!-- 原型: B3 编辑名片 / 职业照裁剪 -->
<script setup lang="ts">
import { showConfirmDialog, showToast } from 'vant'
import { reactive, shallowRef } from 'vue'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import { card as getCard, saveCard, uploadPhoto } from '@/api/generated'
import PageShell from '@/components/common/PageShell.vue'
import ResourceState from '@/components/common/ResourceState.vue'
import PhotoCropper from '@/components/staff/PhotoCropper.vue'
import { useMutation } from '@/composables/useMutation'
import { useResource } from '@/composables/useResource'
const router = useRouter()
const form = reactive({ display_title: '', mobile: '', email: '', intro: '', photo_url: '', photo_bg_url: '', wechat_qr_url: '' })
const background = shallowRef(false); const file = shallowRef<File>(); let baseline = ''
const { saving, failure, run } = useMutation()
const { data, loading, error, reload } = useResource(async () => { const c = await getCard(); Object.assign(form, { display_title: c.display_title, mobile: c.mobile, email: c.email, intro: c.intro, photo_url: c.photo_url, photo_bg_url: c.photo_bg_url, wechat_qr_url: c.wechat_qr_url }); baseline = JSON.stringify(form); background.value = !!c.photo_bg_url; return c })
function choose(event: Event) { const selected = (event.target as HTMLInputElement).files?.[0]; if (!selected) return; if (!selected.type.startsWith('image/') || selected.size > 10 * 1024 * 1024) { showToast('请选择 10MB 以内的图片'); return }; file.value = selected }
async function cropped(photo: File) { if (photo.size > 5 * 1024 * 1024) { showToast('裁剪后图片超过 5MB，请更换照片'); return }; const body = new FormData(); body.append('file', photo); const result = await run(() => uploadPhoto({ body })); if (result) { form.photo_url = result.photo_url; form.photo_bg_url = result.photo_bg_url; file.value = undefined; showToast('职业照已即时保存，其他字段仍需点击保存') } }
async function save() { const result = await run(() => saveCard({ body: { ...form, photo_bg_url: background.value ? form.photo_bg_url || form.photo_url : '' } })); if (result) { baseline = JSON.stringify(form); showToast('已保存，访客端立即生效'); router.push('/staff/card') } }
onBeforeRouteLeave(async () => { if (!baseline || baseline === JSON.stringify(form)) return true; try { await showConfirmDialog({ title: '有未保存的修改', message: '其他未保存字段将丢失；已上传的职业照已即时保存。确定离开？' }); return true } catch { return false } })
</script>
<template><PageShell title="编辑名片" back><template #action><button class="text-button" :disabled="saving || loading" @click="save">保存</button></template><ResourceState :loading="loading" :error="error" @retry="reload"><template v-if="data"><section class="panel stack"><img v-if="form.photo_url" :src="form.photo_url" alt="职业照预览" class="portrait"><div v-else class="empty-inline">尚未上传职业照</div><p class="muted small">原图限 10MB，裁剪后上传限 5MB；职业照上传成功后即时保存。</p><label class="text-button upload-label">更换职业照<input type="file" accept="image/*" aria-label="更换职业照" @change="choose"></label><van-cell title="同时作为对话页背景"><template #right-icon><van-switch v-model="background" aria-label="同时作为对话页背景" size="24" /></template></van-cell></section><van-cell-group inset><van-cell title="姓名" :value="data.name" label="管理员维护" /><van-cell title="部门" :value="data.dept" label="管理员维护" /><van-field v-model="form.display_title" label="展示职位" maxlength="120" /></van-cell-group><van-form @submit="save"><van-field v-model="form.mobile" label="联系电话" type="tel" :rules="[{ pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' }]" /><van-field v-model="form.email" label="邮箱" type="email" /><van-field v-model="form.wechat_qr_url" label="微信二维码" placeholder="填写已上传图片地址" /><p class="muted small">当前上传接口仅支持职业照。微信二维码可填写已有图片地址。</p><van-field v-model="form.intro" label="个人简介" type="textarea" maxlength="150" show-word-limit /><p v-if="failure" class="error" role="alert">{{ failure }}</p><p class="muted">保存后访客端立即生效</p><van-button block type="primary" native-type="submit" :loading="saving">保存</van-button></van-form></template></ResourceState><van-popup :show="!!file" position="bottom" round :close-on-click-overlay="false"><PhotoCropper v-if="file" :file="file" @cropped="cropped" @cancel="file = undefined" /></van-popup></PageShell></template>
<style scoped>.portrait{width:150px;aspect-ratio:3/4;object-fit:cover;margin:auto;border-radius:var(--r-md)}.upload-label{display:grid;justify-items:center}.upload-label input{max-width:100%}</style>
