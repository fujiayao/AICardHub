import type { NotificationData } from '@/api/generated'
import { cardOnly } from '@/platform/release-mode'

export function notificationTarget(notification: Pick<NotificationData, 'target_type' | 'target_id'>): string | undefined {
  const id = notification.target_id
  if (notification.target_type === 'issue') return cardOnly ? undefined : '/staff/assistant'
  if (typeof id !== 'number' || !Number.isSafeInteger(id) || id <= 0) return
  if (notification.target_type === 'lead') return `/staff/customers/${id}`
  if (notification.target_type === 'visitor') return `/staff/customers/${id}?kind=visitor`
  // A session ID is not a visitor ID. Keep unresolved targets in the message centre.
}

export function notificationCopy(notification: Pick<NotificationData, 'target_type' | 'title' | 'content'>) {
  const { target_type: type, title, content } = notification
  if (!cardOnly) return { title, content }
  if (type === 'session' || type === 'issue') return { title: '历史通知', content: '此通知关联的功能暂未开放。' }

  const digest = /^访问(\d+)次，对话\d+次，新线索(\d+)条，初步意向会话\d+个。$/.exec(content)
  return { title, content: digest ? `访问${digest[1]}次，新线索${digest[2]}条。` : content }
}
