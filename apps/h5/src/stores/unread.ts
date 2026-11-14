import { defineStore } from 'pinia'
import { shallowRef } from 'vue'
import { unreadCount } from '@/api/generated'
export const useUnreadStore = defineStore('unread', () => {
 const count = shallowRef(0)
 const error = shallowRef('')
 async function refresh() { try { count.value = (await unreadCount()).count; error.value = '' } catch { error.value = '未读数暂未同步' } }
 return { count, error, refresh }
})
