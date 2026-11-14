import { onMounted, onUnmounted, watch } from 'vue'
import { useUnreadStore } from '@/stores/unread'
export function useUnreadCount() {
 const store = useUnreadStore()
 let timer: ReturnType<typeof setInterval> | undefined
 function visible() { if (timer) clearInterval(timer); if (!document.hidden) { void store.refresh(); timer = setInterval(() => store.refresh(), 30000) } }
 onMounted(() => { visible(); document.addEventListener('visibilitychange', visible) })
 onUnmounted(() => { if (timer) clearInterval(timer); document.removeEventListener('visibilitychange', visible) })
 watch(() => store.count, count => { document.title = `${count ? `(${count}) ` : ''}数科名片` }, { immediate: true })
 return store
}
