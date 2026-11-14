import type { Staff } from '@/api/generated'
import { defineStore } from 'pinia'
import { shallowRef } from 'vue'
import { changePassword, login } from '@/api/generated'
import { clearToken, getToken, setToken } from '@/api/tokens'
export const useAuthStore = defineStore('staff-auth', () => {
 const token = shallowRef(getToken('staff'))
 const staff = shallowRef<Staff>()
 const mustChange = shallowRef(localStorage.getItem('shuke.must-change') === 'true')
 async function signIn(phone: string, password: string) {
  const result = await login({ body: { phone, password } })
  token.value = result.token; staff.value = result.staff
  mustChange.value = result.must_change_pwd
  setToken('staff', result.token); localStorage.setItem('shuke.must-change', String(mustChange.value))
 }
 async function change(old_password: string, new_password: string) {
  await changePassword({ body: { old_password, new_password } })
  signOut()
 }
 function signOut() { token.value = ''; staff.value = undefined; clearToken('staff'); localStorage.removeItem('shuke.must-change'); mustChange.value = false }
 return { token, staff, mustChange, signIn, change, signOut }
})
