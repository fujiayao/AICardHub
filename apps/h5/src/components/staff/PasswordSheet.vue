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
<template><van-popup v-model:show="show" position="bottom" round closeable><section class="sheet stack"><h2>修改密码</h2><van-form @submit="submit"><van-field v-model="form.old" label="原密码" type="password" autocomplete="current-password" /><van-field v-model="form.next" label="新密码" type="password" autocomplete="new-password" /><van-field v-model="form.confirm" label="确认密码" type="password" autocomplete="new-password" /><p class="muted">8–20 位，包含字母和数字，两次输入一致</p><p v-if="failure" class="error" role="alert">{{ failure }}</p><van-button block type="primary" native-type="submit" :disabled="!valid || !form.old" :loading="saving">保存</van-button></van-form></section></van-popup></template>
