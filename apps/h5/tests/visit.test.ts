import { beforeEach, describe, expect, it, vi } from 'vitest'
import { sceneKey } from '../src/utils/scene'

const createVisit = vi.hoisted(() => vi.fn())
vi.mock('../src/api/generated', () => ({ createVisit }))

const store = new Map<string, string>()
vi.stubGlobal('sessionStorage', {
  getItem: (k: string) => store.get(k) ?? null,
  setItem: (k: string, v: string) => { store.set(k, v) },
  removeItem: (k: string) => { store.delete(k) },
})

const { cachedVisit, ensureVisit } = await import('../src/composables/useVisit')
const ensure = () => Promise.resolve()

describe('visit reuse across card home and chat', () => {
  beforeEach(() => { store.clear(); createVisit.mockReset() })

  it('reuses a cached scene visit without creating another', async () => {
    store.set(sceneKey('sk01', 3, 'qr'), '42')
    expect(cachedVisit('sk01', 3, 'qr')).toBe(42)
    const id = await ensureVisit(ensure, 'sk01', 3, 'qr')
    expect(id).toBe(42)
    expect(createVisit).not.toHaveBeenCalled()
  })

  it('single-flights concurrent home+chat requests into one createVisit', async () => {
    createVisit.mockResolvedValue({ visit_id: 7 })
    const [a, b] = await Promise.all([
      ensureVisit(ensure, 'sk01', undefined, 'link'),
      ensureVisit(ensure, 'sk01', undefined, 'link'),
    ])
    expect(a).toBe(7); expect(b).toBe(7)
    expect(createVisit).toHaveBeenCalledTimes(1)
    expect(cachedVisit('sk01', undefined, 'link')).toBe(7)
  })

  it('keeps different sources/campaigns in separate visits', async () => {
    createVisit.mockResolvedValueOnce({ visit_id: 1 }).mockResolvedValueOnce({ visit_id: 2 })
    await ensureVisit(ensure, 'sk01', undefined, 'nfc')
    await ensureVisit(ensure, 'sk01', 5, 'poster')
    expect(createVisit).toHaveBeenCalledTimes(2)
    expect(cachedVisit('sk01', undefined, 'nfc')).toBe(1)
    expect(cachedVisit('sk01', 5, 'poster')).toBe(2)
  })

  it('home forceNew creates a fresh visit even when a cached one exists', async () => {
    store.set(sceneKey('sk01', undefined, 'nfc'), '11')
    createVisit.mockResolvedValue({ visit_id: 12 })
    const id = await ensureVisit(ensure, 'sk01', undefined, 'nfc', { forceNew: true })
    expect(id).toBe(12)
    expect(createVisit).toHaveBeenCalledTimes(1)
    expect(cachedVisit('sk01', undefined, 'nfc')).toBe(12)
  })

  it('chat reuses the pending home visit instead of the stale cache or a duplicate', async () => {
    store.set(sceneKey('sk01', 2, 'qr'), '20')
    let resolve!: (v: { visit_id: number }) => void
    createVisit.mockReturnValue(new Promise((r) => { resolve = r }))
    const home = ensureVisit(ensure, 'sk01', 2, 'qr', { forceNew: true })
    const chat = ensureVisit(ensure, 'sk01', 2, 'qr')
    await Promise.resolve(); resolve({ visit_id: 21 })
    expect(await home).toBe(21); expect(await chat).toBe(21)
    expect(createVisit).toHaveBeenCalledTimes(1)
  })

  it('does not share a pending home visit across sources', async () => {
    createVisit.mockResolvedValueOnce({ visit_id: 31 }).mockResolvedValueOnce({ visit_id: 32 })
    const home = ensureVisit(ensure, 'sk01', undefined, 'nfc', { forceNew: true })
    const chat = ensureVisit(ensure, 'sk01', undefined, 'poster')
    expect(await home).toBe(31); expect(await chat).toBe(32)
    expect(createVisit).toHaveBeenCalledTimes(2)
  })

  it('direct chat without cache creates exactly one visit and caches it', async () => {
    createVisit.mockResolvedValue({ visit_id: 41 })
    expect(await ensureVisit(ensure, 'sk02', undefined, 'link')).toBe(41)
    expect(await ensureVisit(ensure, 'sk02', undefined, 'link')).toBe(41)
    expect(createVisit).toHaveBeenCalledTimes(1)
  })
})
