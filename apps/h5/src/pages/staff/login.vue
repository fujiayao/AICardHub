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
 const wasChanging = changing.value
 const result = await run(async () => {
  if (wasChanging) { await auth.change(form.password, form.newPassword); return true }
  await auth.signIn(form.phone, form.password); return !auth.mustChange
 })
 if (!result) return
 if (wasChanging) {
  form.password = ''; form.newPassword = ''; form.confirm = ''; visible.value = false
  await router.replace({ path: '/staff/login', query: { password_changed: '1', redirect: safeReturn(route.query.redirect) } })
 } else await router.replace(safeReturn(route.query.redirect))
}
</script>
<template><main class="login-page"><header class="masthead"><span class="brand-mark">数</span><div><h1>数科名片</h1><p class="muted">员工端 · 让每一次交流都有回应</p></div></header><section class="panel stack form-panel"><h2>{{ changing ? '设置新密码' : '欢迎回来' }}</h2><p v-if="route.query.password_changed === '1' && !changing" role="status" class="notice">密码已修改，请重新登录</p><p v-if="changing" class="notice">首次登录请先修改初始密码</p><van-form @submit="submit"><van-field v-if="!changing" v-model="form.phone" label="手机号" type="tel" autocomplete="username" maxlength="11" placeholder="请输入手机号" :rules="[{ pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' }]" /><van-field v-model="form.password" :label="changing ? '原密码' : '密码'" :type="visible ? 'text' : 'password'" autocomplete="current-password" :rules="[{ required: true, message: '请输入密码' }]"><template #button><button type="button" class="text-button" aria-label="切换密码可见性" @click="visible = !visible">{{ visible ? '隐藏' : '显示' }}</button></template></van-field><template v-if="changing"><van-field v-model="form.newPassword" label="新密码" type="password" autocomplete="new-password" maxlength="20" placeholder="8–20 位，含字母和数字" /><van-field v-model="form.confirm" label="确认密码" type="password" autocomplete="new-password" placeholder="再次输入新密码" /><div class="password-rules"><p :class="{ success: validPassword }"><span class="icon" :class="validPassword ? 'i-lucide-check' : 'i-lucide-circle'" aria-hidden="true" />8–20 位，含字母和数字</p><p :class="{ success: !!form.confirm && form.confirm === form.newPassword }"><span class="icon" :class="!!form.confirm && form.confirm === form.newPassword ? 'i-lucide-check' : 'i-lucide-circle'" aria-hidden="true" />两次输入一致</p></div></template><p v-if="failure" class="error" role="alert">{{ failure }}</p><van-button block type="primary" native-type="submit" :loading="saving" :disabled="changing ? !validPassword || form.confirm !== form.newPassword || !form.password : !form.phone || !form.password">{{ changing ? '确认并进入' : '登录' }}</van-button></van-form></section><p class="muted help">账号由管理员开通，忘记密码请联系管理员</p></main></template>
<style scoped>
.login-page{padding:72px 24px 40px;min-height:100dvh}
.masthead{display:flex;align-items:center;gap:var(--sp-4);margin-bottom:var(--sp-7)}
.brand-mark{display:grid;place-items:center;background:var(--c-ink);color:var(--c-surface);width:56px;height:56px;border-radius:var(--r-lg);font-size:var(--fs-xl);flex-shrink:0}
.masthead h1{font-size:var(--fs-xl);line-height:1.2}
.masthead .muted{font-size:var(--fs-sm);margin-top:4px}
.form-panel{padding:var(--sp-6) var(--sp-5)}
.van-button{margin-top:var(--sp-6)}
.help{text-align:center;margin-top:var(--sp-6);font-size:var(--fs-sm)}
.password-rules{display:grid;gap:var(--sp-2);padding:var(--sp-3) var(--sp-1) 0;font-size:var(--fs-sm);color:var(--c-text-2)}
.password-rules p{display:flex;align-items:center;gap:6px}
.password-rules .success{color:var(--c-success)}
</style>
