import { defineStore } from 'pinia'
import { shallowRef } from 'vue'
import { ApiError } from '@/api/client'
import { initVisitor } from '@/api/generated'
import { clearToken, setToken } from '@/api/tokens'
export const useVisitorStore = defineStore('visitor', () => {
 const ready = shallowRef(false)
 let pending: Promise<void> | undefined
 async function initialize() {
  try { const result = await initVisitor({ body: {} }); setToken('visitor', result.visitor_token) }
  catch (e) {
   if (!(e instanceof ApiError) || e.status !== 401) throw e
   clearToken('visitor')
   const result = await initVisitor({ body: {} }); setToken('visitor', result.visitor_token)
  }
  ready.value = true
 }
 function ensure() { if (ready.value) return Promise.resolve(); if (!pending) pending = initialize().finally(() => { pending = undefined }); return pending }
 function reset() { ready.value = false; clearToken('visitor') }
 return { ready, ensure, reset }
})
