<!-- 原型: B3 编辑名片 / 职业照裁剪 -->
<script setup lang="ts">
import type { FormInstance } from 'vant'
import { showConfirmDialog, showToast } from 'vant'
import { reactive, shallowRef, useTemplateRef } from 'vue'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import { card as getCard, saveCard, uploadPhoto } from '@/api/generated'
import AnonymousPortrait from '@/components/common/AnonymousPortrait.vue'
import PageShell from '@/components/common/PageShell.vue'
import ResourceState from '@/components/common/ResourceState.vue'
import PhotoCropper from '@/components/staff/PhotoCropper.vue'
import WechatQRUpload from '@/components/staff/WechatQRUpload.vue'
import { useMutation } from '@/composables/useMutation'
import { useResource } from '@/composables/useResource'

const router = useRouter()
const form = reactive({ display_title: '', mobile: '', email: '', intro: '', photo_url: '', photo_bg_url: '', wechat_qr_url: '' })
const uploadingQR = shallowRef(false)
const background = shallowRef(false)
const file = shallowRef<File>()
const formRef = useTemplateRef<FormInstance>('formRef')
let baseline = ''
const { saving, failure, run } = useMutation()
const { data, loading, error, reload } = useResource(async () => {
  const c = await getCard()
  Object.assign(form, { display_title: c.display_title, mobile: c.mobile, email: c.email, intro: c.intro, photo_url: c.photo_url, photo_bg_url: c.photo_bg_url, wechat_qr_url: c.wechat_qr_url })
  baseline = JSON.stringify(form)
  background.value = !!c.photo_bg_url
  return c
})

// 仅校验已填写的内容；未填写时视为有效（手机、邮箱均为选填）。
const mobileRules = [{ validator: (v: string) => !v || /^1[3-9]\d{9}$/.test(v), message: '请输入正确的手机号' }]
const emailRules = [{ validator: (v: string) => !v || /^[^\s@]+@[^\s@][^\s.@]*\.[^\s@]+$/.test(v), message: '请输入正确的邮箱' }]

function choose(event: Event) {
  const selected = (event.target as HTMLInputElement).files?.[0]
  if (!selected) return
  if (!selected.type.startsWith('image/') || selected.size > 10 * 1024 * 1024) { showToast('请选择 10MB 以内的图片'); return }
  file.value = selected
}
async function cropped(photo: File) {
  if (photo.size > 5 * 1024 * 1024) { showToast('裁剪后图片超过 5MB，请更换照片'); return }
  const body = new FormData()
  body.append('file', photo)
  const result = await run(() => uploadPhoto({ body }))
  if (result) { form.photo_url = result.photo_url; form.photo_bg_url = result.photo_bg_url; file.value = undefined; showToast('职业照已即时保存，其他字段仍需点击保存') }
}
function qrUploaded(url: string) {
  form.wechat_qr_url = url
  if (baseline) baseline = JSON.stringify({ ...JSON.parse(baseline), wechat_qr_url: url })
}
// 顶部“保存”走与表单提交完全相同的校验链路。
function submitFromHeader() {
  if (saving.value || loading.value || uploadingQR.value) return
  formRef.value?.submit()
}
async function save() {
  if (uploadingQR.value) return
  const result = await run(() => saveCard({ body: { ...form, photo_bg_url: background.value ? form.photo_bg_url || form.photo_url : '' } }))
  if (result) { baseline = JSON.stringify(form); showToast('已保存，访客端立即生效'); router.push('/staff/card') }
}
onBeforeRouteLeave(async () => {
  if (!baseline || baseline === JSON.stringify(form)) return true
  try { await showConfirmDialog({ title: '有未保存的修改', message: '其他未保存字段将丢失；已上传的图片已即时保存。确定离开？' }); return true } catch { return false }
})
</script>

<template>
  <PageShell title="编辑名片" back>
    <template #action>
      <button class="text-button" :disabled="saving || loading || uploadingQR" @click="submitFromHeader">保存</button>
    </template>
    <ResourceState :loading="loading" :error="error" @retry="reload">
      <van-form v-if="data" ref="formRef" class="b3" @submit="save">
        <h2 class="sec-title">职业照</h2>
        <div class="group portrait-group">
          <div class="portrait">
            <img v-if="form.photo_url" :src="form.photo_url" alt="职业照预览">
            <AnonymousPortrait v-else />
          </div>
          <div class="portrait-side">
            <p class="hint">竖版、正面半身、背景简洁，访客第一眼看到的就是它。</p>
            <label class="change-btn">
              <span class="icon i-lucide-image" aria-hidden="true" />更换职业照
              <input type="file" accept="image/*" aria-label="更换职业照" @change="choose">
            </label>
            <p class="hint tiny">原图限 10MB，裁剪后上传限 5MB；上传成功即时保存。</p>
          </div>
        </div>

        <div class="group single">
          <van-cell title="同时作为对话页背景" label="访客和 AI 分身聊天时显示为模糊背景">
            <template #right-icon><van-switch v-model="background" aria-label="同时作为对话页背景" size="24" /></template>
          </van-cell>
        </div>

        <h2 class="sec-title">基础信息</h2>
        <div class="group fields">
          <van-cell title="姓名" :value="data.name || '—'" label="管理员维护" />
          <van-field v-model="form.display_title" label="展示职位" placeholder="如：解决方案顾问" maxlength="120" />
          <van-cell title="部门" :value="data.dept || '—'" label="管理员维护" />
          <van-cell title="公司" :value="data.company_name || '—'" label="管理员维护" />
        </div>

        <h2 class="sec-title">联系方式</h2>
        <div class="group fields">
          <van-field v-model="form.mobile" label="手机" type="tel" placeholder="选填" :rules="mobileRules" />
          <van-field v-model="form.email" label="邮箱" type="email" placeholder="选填" :rules="emailRules" />
          <WechatQRUpload :value="form.wechat_qr_url" :disabled="saving" @uploaded="qrUploaded" @clear="form.wechat_qr_url = ''" @busy="uploadingQR = $event" />
        </div>

        <h2 class="sec-title">个人简介<small>选填</small></h2>
        <div class="group intro">
          <van-field v-model="form.intro" type="textarea" maxlength="150" rows="4" autosize show-word-limit placeholder="一句话介绍你擅长的领域与行业" />
        </div>

        <p v-if="failure" class="error" role="alert">{{ failure }}</p>
        <p class="hint foot">保存后访客端立即生效。部门、公司等信息由管理员维护。</p>
      </van-form>
    </ResourceState>
    <van-popup :show="!!file" position="bottom" round :close-on-click-overlay="false">
      <PhotoCropper v-if="file" :file="file" @cropped="cropped" @cancel="file = undefined" />
    </van-popup>
  </PageShell>
</template>

<style scoped>
/* 本页去掉 PageShell .content 的 grid 间距与内边距，改用原型的区块外边距 */
:deep(.content) { display: block; padding: 0; }
.sec-title { display: flex; align-items: center; gap: 6px; padding: 20px 16px 10px; font-size: var(--fs-md); font-weight: 600; color: var(--c-ink); }
.sec-title small { font-size: var(--fs-sm); font-weight: 400; color: var(--c-text-3); }
.group { margin: 0 16px; background: var(--c-surface); border-radius: var(--r-lg); overflow: hidden; }
.group.fields :deep(.van-cell),
.group.single :deep(.van-cell),
.group.intro :deep(.van-cell) { background: var(--c-surface); }
.portrait-group { display: flex; gap: 14px; align-items: flex-end; padding: 14px 16px; }
.portrait { width: 96px; height: 128px; flex: none; border-radius: var(--r-md); overflow: hidden; background: var(--c-bg); }
.portrait img { width: 100%; height: 100%; object-fit: cover; }
.portrait-side { flex: 1; min-width: 0; display: grid; gap: 10px; }
.hint { font-size: var(--fs-sm); color: var(--c-text-3); line-height: 1.5; margin: 0; }
.hint.tiny { font-size: var(--fs-xs); }
.change-btn { display: inline-flex; align-items: center; gap: 6px; align-self: flex-start; padding: 7px 14px; border-radius: var(--r-md); background: var(--c-primary-soft); color: var(--c-primary); font-size: var(--fs-sm); }
.change-btn input { display: none; }
.change-btn .icon { width: 16px; height: 16px; }
.foot { padding: 12px 16px 24px; }
.error { padding: 8px 16px 0; }
</style>
