import { afterEach, describe, expect, it, vi } from 'vitest'
import { isMiniProgram, miniCardSharePath, openMiniCardShare } from '../src/platform/mini-program'

const { toast } = vi.hoisted(() => ({ toast: vi.fn() }))
vi.mock('vant', () => ({ showToast: toast }))

afterEach(() => { vi.unstubAllGlobals(); toast.mockClear() })

describe('mini program routing', () => {
  it('only writes public card and activity data to the native bridge route', () => {
    expect(miniCardSharePath('card:one', 37)).toBe('/pages/share/index?code=card%3Aone&s=link&e=37')
    expect(miniCardSharePath('card-one')).toBe('/pages/share/index?code=card-one&s=link')
    for (const code of ['', 'a'.repeat(33), '../admin', 'a&s=qr', 'http://example.test', 'token%2f', 'staff\n']) {
      expect(miniCardSharePath(code)).toBeUndefined()
    }
    for (const event of [0, -1, 1.5, Infinity, Number.MAX_SAFE_INTEGER + 1]) {
      expect(miniCardSharePath('card-one', event)).toBeUndefined()
    }
  })

  it('leaves normal WeChat and browser sharing untouched', () => {
    vi.stubGlobal('window', { navigator: { userAgent: 'MicroMessenger/8.0' } })
    expect(isMiniProgram()).toBe(false)
    expect(openMiniCardShare('card-one', 37)).toBe(false)
    expect(toast).not.toHaveBeenCalled()
  })

  it('recognizes mini-program environments by UA or injected bridge flag', () => {
    vi.stubGlobal('window', { navigator: { userAgent: 'MicroMessenger/8.0 miniProgram/wx-example' } })
    expect(isMiniProgram()).toBe(true)
    vi.stubGlobal('window', { __wxjs_environment: 'miniprogram', navigator: { userAgent: 'MicroMessenger/8.0' } })
    expect(isMiniProgram()).toBe(true)
  })

  it('navigates to the native share page, with a staff-specific fallback', async () => {
    const navigateTo = vi.fn(({ fail }: { fail: () => void }) => fail())
    vi.stubGlobal('window', { __wxjs_environment: 'miniprogram', wx: { miniProgram: { navigateTo } } })
    expect(openMiniCardShare('card-one', 37, true)).toBe(true)
    await vi.waitFor(() => {
      expect(navigateTo).toHaveBeenCalledWith({ url: '/pages/share/index?code=card-one&s=link&e=37', fail: expect.any(Function) })
      expect(toast).toHaveBeenCalledWith('暂时无法转发，可改用「链接」或「二维码」')
    })
  })
})
