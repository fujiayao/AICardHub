import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useAuthStore } from '../src/stores/auth'

const api = vi.hoisted(() => ({ login: vi.fn(), changePassword: vi.fn() }))
vi.mock('../src/api/generated', () => api)

describe('password change ends the staff session', () => {
  beforeEach(() => {
    const values = new Map<string, string>()
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => values.set(key, value),
      removeItem: (key: string) => values.delete(key),
    })
    api.login.mockReset(); api.changePassword.mockReset()
    setActivePinia(createPinia())
  })

  it('clears staff token and first-password flag after success, preserving visitor token', async () => {
    api.login.mockResolvedValue({ token: 'old-staff-token', must_change_pwd: true, staff: { id: 1 } })
    api.changePassword.mockResolvedValue({ ok: true })
    localStorage.setItem('shuke.visitor.token', 'visitor-token')
    const auth = useAuthStore()
    await auth.signIn('13900000000', 'old')
    await auth.change('old', 'NewPassword123')
    expect(auth.token).toBe(''); expect(auth.staff).toBeUndefined(); expect(auth.mustChange).toBe(false)
    expect(localStorage.getItem('shuke.staff.token')).toBeNull()
    expect(localStorage.getItem('shuke.must-change')).toBeNull()
    expect(localStorage.getItem('shuke.visitor.token')).toBe('visitor-token')
  })

  it('preserves the current session when the password change is rejected', async () => {
    api.login.mockResolvedValue({ token: 'current-staff-token', must_change_pwd: false, staff: { id: 1 } })
    api.changePassword.mockRejectedValue(new Error('原密码错误'))
    const auth = useAuthStore()
    await auth.signIn('13900000000', 'old')
    await expect(auth.change('incorrect', 'NewPassword123')).rejects.toThrow('原密码错误')
    expect(auth.token).toBe('current-staff-token')
    expect(localStorage.getItem('shuke.staff.token')).toBe('current-staff-token')
  })
})
