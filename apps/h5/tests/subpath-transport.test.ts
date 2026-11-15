import { afterEach, describe, expect, it, vi } from 'vitest'
import { request } from '../src/api/client'
import { streamChat } from '../src/api/sse'

const transport = vi.hoisted(() => ({ request: vi.fn() }))
vi.mock('axios', () => ({ default: { create: () => transport, isAxiosError: () => false } }))
vi.mock('vant', () => ({ showToast: vi.fn() }))

afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); vi.clearAllMocks() })

describe.each(['/', '/aicardhub/'])('real transport prefix %s', (base) => {
  const prefix = base === '/' ? '' : '/aicardhub'
  it('prefixes generated API requests and maps nested assets without corrupting outgoing paths', async () => {
    vi.stubEnv('BASE_URL', base)
    vi.stubGlobal('localStorage', { getItem: () => 'token' })
    transport.request.mockResolvedValue({ data: { company: { logo_url: '/files/logo.png' } } })
    const result = await request<{ company: { logo_url: string } }>('put', '/api/v1/me/card', { photo_url: `${prefix}/files/photo.png`, intro: '/files/prose' }, 'staff')
    expect(transport.request).toHaveBeenCalledWith(expect.objectContaining({ url: `${prefix}/api/v1/me/card`, data: { photo_url: '/files/photo.png', intro: '/files/prose' } }))
    expect(result.company.logo_url).toBe(`${prefix}/files/logo.png`)
  })

  it('prefixes SSE while preserving authorization, signal and streaming events', async () => {
    vi.stubEnv('BASE_URL', base)
    vi.stubGlobal('localStorage', { getItem: () => 'visitor-token' })
    const fetcher = vi.fn().mockResolvedValue(new Response('event: delta\ndata: {"text":"回答"}\n\n', { status: 200 }))
    vi.stubGlobal('fetch', fetcher)
    const controller = new AbortController(); const event = vi.fn()
    await streamChat('/api/v1/public/chat/sessions/7/messages', '问题', 'visitor', controller.signal, event)
    expect(fetcher).toHaveBeenCalledWith(`${prefix}/api/v1/public/chat/sessions/7/messages`, expect.objectContaining({ signal: controller.signal, headers: expect.objectContaining({ Authorization: 'Bearer visitor-token' }) }))
    expect(event).toHaveBeenCalledWith({ event: 'delta', data: { text: '回答' } })
  })

  it('downloads vCard from the deployed base', async () => {
    vi.stubEnv('BASE_URL', base)
    vi.stubGlobal('navigator', { userAgent: 'test' })
    const assign = vi.fn()
    vi.stubGlobal('window', { location: { assign } })
    const { saveContact } = await import('../src/platform')
    saveContact('one')
    expect(assign).toHaveBeenCalledExactlyOnceWith(`${prefix}/api/v1/public/cards/one/vcard`)
  })
})
