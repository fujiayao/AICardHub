<script setup lang="ts">
import { showToast } from 'vant'
import { computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useMutation } from '@/composables/useMutation'
import { useAuthStore } from '@/stores/auth'
const show = defineModel<boolean>({ default: false }); const auth = useAuthStore()
const router = useRouter()
const form = reactive({ old: '', next: '', confirm: '' })
const valid = computed(() => form.next.length >= 8 && form.next.length <= 20 && /[a-z]/i.test(form.next) && /\d/.test(form.next) && form.next === form.confirm)
const { saving, failure, run } = useMutation()
async function submit() {
 const result = await run(async () => { await auth.change(form.old, form.next); return true })
 if (result) {
  showToast('密码已修改，请重新登录'); show.value = false
  form.old = ''; form.next = ''; form.confirm = ''
  await router.replace({ path: '/staff/login', query: { password_changed: '1' } })
 }
}
</script>
<template><van-popup v-model:show="show" position="bottom" round closeable><section class="sheet stack"><header class="sheet-head"><span class="icon i-lucide-lock head-icon" aria-hidden="true" /><h2>修改密码</h2></header><van-form @submit="submit"><van-cell-group inset><van-field v-model="form.old" label="原密码" type="password" autocomplete="current-password" placeholder="请输入原密码" /></van-cell-group><van-cell-group inset><van-field v-model="form.next" label="新密码" type="password" autocomplete="new-password" placeholder="8–20 位，含字母和数字" /><van-field v-model="form.confirm" label="确认密码" type="password" autocomplete="new-password" placeholder="再次输入新密码" /></van-cell-group><p class="muted small help">8–20 位，包含字母和数字，两次输入一致</p><p v-if="failure" class="error" role="alert">{{ failure }}</p><div class="actions"><van-button block type="primary" native-type="submit" :disabled="!valid || !form.old" :loading="saving">保存</van-button></div></van-form></section></van-popup></template>
<style scoped>
.sheet-head{display:flex;align-items:center;gap:var(--sp-2)}
.head-icon{color:var(--c-text-2)}
.help{padding:0 var(--sp-1)}
.actions{margin-top:var(--sp-2)}
</style>
