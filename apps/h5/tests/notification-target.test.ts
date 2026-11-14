import { describe, expect, it } from 'vitest'
import { notificationTarget } from '../src/utils/notification-target'

describe('notification target identity', () => {
  it('keeps lead and visitor identifiers on distinct routes', () => {
    expect(notificationTarget({ target_type: 'lead', target_id: 17 })).toBe('/staff/customers/17')
    expect(notificationTarget({ target_type: 'visitor', target_id: 17 })).toBe('/staff/customers/17?kind=visitor')
    expect(notificationTarget({ target_type: 'issue', target_id: 17 })).toBe('/staff/assistant')
  })
  it('does not turn session IDs, absent or invalid IDs into customer routes', () => {
    expect(notificationTarget({ target_type: 'session', target_id: 17 })).toBeUndefined()
    for (const id of [null, undefined, 0, -1, 1.2]) expect(notificationTarget({ target_type: 'lead', target_id: id })).toBeUndefined()
    expect(notificationTarget({})).toBeUndefined()
  })
})
