import { onMounted, ref, shallowRef } from 'vue'
import { errorMessage } from '@/api/client'
export function usePaged<T>(loader: (page: number) => Promise<{ items: T[], total: number }>) {
 const items = ref<T[]>([]) as import('vue').Ref<T[]>
 const loading = shallowRef(false); const refreshing = shallowRef(false); const error = shallowRef(''); const finished = shallowRef(false); const total = shallowRef(0)
 let page = 0; let revision = 0
 async function load(reset = false) {
  if (loading.value && !reset) return
  const current = ++revision; const next = reset ? 1 : page + 1
  loading.value = true; error.value = ''
  try { const data = await loader(next); if (current !== revision) return; items.value = reset ? data.items : [...items.value, ...data.items]; total.value = data.total; page = next; finished.value = !data.items.length || items.value.length >= data.total }
  catch (e) { if (current === revision) error.value = errorMessage(e) }
  finally { if (current === revision) { loading.value = false; refreshing.value = false } }
 }
 function refresh() { finished.value = false; return load(true) }
 onMounted(refresh)
 return { items, total, loading, refreshing, error, finished, load, refresh }
}
