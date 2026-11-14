import { defineStore } from 'pinia'
import { shallowRef } from 'vue'
import { health } from '@/api/generated'
export const useModelStore = defineStore('model', () => {
 const mode = shallowRef(''); const error = shallowRef(''); let pending: Promise<void> | undefined
 function ensure() { if (pending) return pending; pending = health().then(result => { mode.value = result.llm_mode; error.value = '' }).catch(() => { error.value = '模型状态暂不可用，请以回答标记为准' }); return pending }
 return { mode, error, ensure }
})
