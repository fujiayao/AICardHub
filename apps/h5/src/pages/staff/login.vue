<!-- 原型: B1 登录 / 首次改密 -->
<script setup lang="ts">
import { computed, reactive, shallowRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMutation } from '@/composables/useMutation'
import { safeReturn } from '@/platform'
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore(); const route = useRoute(); const router = useRouter()
const form = reactive({ phone: '', password: '', newPassword: '', confirm: '' })
const visible = shallowRef(false)
const changing = computed(() => auth.mustChange || route.query.change === '1')
const validPassword = computed(() => form.newPassword.length >= 8 && form.newPassword.length <= 20 && /[a-z]/i.test(form.newPassword) && /\d/.test(form.newPassword))
const { saving, failure, run } = useMutation()
async function submit() {
 const result = await run(async () => {
  if (changing.value) { await auth.change(form.password, form.newPassword); return true }
  await auth.signIn(form.phone, form.password); return !auth.mustChange
 })
 if (result) router.replace(safeReturn(route.query.redirect))
}
</script>
<template><main class="login-page"><div class="brand"><span class="brand-mark">数</span><h1>数科名片</h1><p class="muted">员工端 · 让每一次交流都有回应</p></div><section class="panel stack"><h2>{{ changing ? '设置新密码' : '欢迎回来' }}</h2><p v-if="changing" class="notice">首次登录请先修改初始密码</p><van-form @submit="submit"><van-field v-if="!changing" v-model="form.phone" label="手机号" type="tel" autocomplete="username" maxlength="11" placeholder="请输入手机号" :rules="[{ pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' }]" /><van-field v-model="form.password" :label="changing ? '原密码' : '密码'" :type="visible ? 'text' : 'password'" autocomplete="current-password" :rules="[{ required: true, message: '请输入密码' }]"><template #button><button type="button" class="text-button" aria-label="切换密码可见性" @click="visible = !visible">{{ visible ? '隐藏' : '显示' }}</button></template></van-field><template v-if="changing"><van-field v-model="form.newPassword" label="新密码" type="password" autocomplete="new-password" maxlength="20" /><van-field v-model="form.confirm" label="确认密码" type="password" autocomplete="new-password" /><div class="password-rules muted"><p :class="{ success: validPassword }">8–20 位，含字母和数字</p><p :class="{ success: !!form.confirm && form.confirm === form.newPassword }">两次输入一致</p></div></template><p v-if="failure" class="error" role="alert">{{ failure }}</p><van-button block type="primary" native-type="submit" :loading="saving" :disabled="changing ? !validPassword || form.confirm !== form.newPassword || !form.password : !form.phone || !form.password">{{ changing ? '确认并进入' : '登录' }}</van-button></van-form></section><p class="muted help">账号由管理员开通，忘记密码请联系管理员</p></main></template>
<style scoped>.login-page{padding:64px 24px;min-height:100dvh}.brand{text-align:center;margin-bottom:40px}.brand-mark{display:inline-grid;place-items:center;background:var(--c-ink);color:var(--c-surface);width:64px;height:64px;border-radius:var(--r-lg);font-size:var(--fs-xxl);margin-bottom:16px}.brand h1{margin-bottom:8px}.van-button{margin-top:24px}.help{text-align:center;margin-top:24px}.password-rules{padding:12px 16px}</style>
