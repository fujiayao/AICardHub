import { shallowRef } from 'vue'
import { errorMessage } from '@/api/client'
export function useMutation() {
 const saving = shallowRef(false)
 const failure = shallowRef('')
 async function run<T>(action: () => Promise<T>): Promise<T | undefined> {
  if (saving.value) return
  saving.value = true; failure.value = ''
  try { return await action() } catch (e) { failure.value = errorMessage(e) }
  finally { saving.value = false }
 }
 return { saving, failure, run }
}
