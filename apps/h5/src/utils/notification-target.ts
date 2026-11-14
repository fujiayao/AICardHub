import type { NotificationData } from '@/api/generated'

export function notificationTarget(notification: Pick<NotificationData, 'target_type' | 'target_id'>): string | undefined {
  const id = notification.target_id
  if (notification.target_type === 'issue') return '/staff/assistant'
  if (typeof id !== 'number' || !Number.isSafeInteger(id) || id <= 0) return
  if (notification.target_type === 'lead') return `/staff/customers/${id}`
  if (notification.target_type === 'visitor') return `/staff/customers/${id}?kind=visitor`
  // A session ID is not a visitor ID. Keep unresolved targets in the message centre.
}
