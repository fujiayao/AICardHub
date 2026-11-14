import { onMounted, onScopeDispose, shallowRef } from 'vue'
import { errorMessage } from '@/api/client'
export function useResource<T>(loader: () => Promise<T>, immediate = true) {
 const data = shallowRef<T>()
 const loading = shallowRef(false)
 const error = shallowRef('')
 let revision = 0
 async function reload() {
  const current = ++revision
  loading.value = true; error.value = ''
  try { const result = await loader(); if (current === revision) data.value = result }
  catch (e) { if (current === revision) error.value = errorMessage(e) }
  finally { if (current === revision) loading.value = false }
 }
 onScopeDispose(() => { revision++ })
 if (immediate) onMounted(reload)
 return { data, loading, error, reload }
}
