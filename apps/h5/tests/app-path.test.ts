import { afterEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { cardShareUrl, mapAssetPaths, normalizeBase, publicUrl, vcardPath, withAppBase } from '../src/utils/app-path'

afterEach(() => vi.unstubAllEnvs())

describe.each(['/', '/aicardhub/'])('deployment base %s', (base) => {
  const prefix = base === '/' ? '' : '/aicardhub'
  it('prefixes API and asset paths once, preserving query and external URLs', () => {
    vi.stubEnv('BASE_URL', base)
    for (const path of ['/api/v1/public/cards/one', '/files/photo.png?size=72', '/c/one?s=qr&e=42']) {
      expect(withAppBase(path)).toBe(`${prefix}${path}`)
      expect(withAppBase(withAppBase(path))).toBe(`${prefix}${path}`)
    }
    for (const value of ['https://cdn.example/files/a.png', '//cdn.example/a.png', 'data:image/png;base64,a', 'blob:local', '#photo'])
      expect(withAppBase(value)).toBe(value)
  })

  it('builds share and vCard destinations without modifying router logical paths', () => {
    vi.stubEnv('BASE_URL', base)
    expect(cardShareUrl('one', 's=nfc&e=42', 'https://haiwex.com')).toBe(`https://haiwex.com${prefix}/c/one?s=nfc&e=42`)
    expect(vcardPath('a/b')).toBe(`${prefix}/api/v1/public/cards/a%2Fb/vcard`)
    expect(publicUrl('https://haiwex.com/c/one?s=poster', 'https://haiwex.com')).toBe(`https://haiwex.com${prefix}/c/one?s=poster`)
    expect(publicUrl(`https://haiwex.com${prefix}/c/one`, 'https://haiwex.com')).toBe(`https://haiwex.com${prefix}/c/one`)
    expect(publicUrl('https://other.example/c/one', 'https://haiwex.com')).toBe('https://other.example/c/one')
  })

  it('lets Vue Router generate base-prefixed hrefs from unchanged logical navigation', async () => {
    const router = createRouter({ history: createMemoryHistory(base), routes: [
      { path: '/card/:code', component: {} }, { path: '/chat/:code', component: {} },
    ] })
    await router.push({ path: '/card/one', query: { s: 'nfc', e: '42' } })
    expect(router.currentRoute.value.fullPath).toBe('/card/one?s=nfc&e=42')
    expect(router.resolve({ path: '/chat/one', query: { s: 'nfc', e: '42' } }).href).toBe(`${prefix}/chat/one?s=nfc&e=42`)
  })

  it('maps only known asset fields and restores storage paths when saving', () => {
    vi.stubEnv('BASE_URL', base)
    const original = {
      photo_url: '/files/photo.png', company: { logo_url: '/files/logo.svg', intro: '/files/keep-this-text' },
      products: [{ image_url: 'https://cdn.example/a.png', summary: '/files/not-an-image' }],
      content: '请看 /files/manual.pdf', short_url: 'https://other.example/c/one', unknown_url: '/files/no.png',
    }
    const display = mapAssetPaths(original)
    expect(display.photo_url).toBe(`${prefix}/files/photo.png`)
    expect(display.company.logo_url).toBe(`${prefix}/files/logo.svg`)
    expect(display.company.intro).toBe(original.company.intro)
    expect(display.products).toEqual(original.products)
    expect(display.content).toBe(original.content)
    expect(display.unknown_url).toBe(original.unknown_url)
    expect(mapAssetPaths(display)).toEqual(display)
    expect(mapAssetPaths(display, 'storage')).toEqual(original)
    expect(original.photo_url).toBe('/files/photo.png')
    const upload = new FormData()
    upload.append('file', new Blob(['image']))
    expect(mapAssetPaths(upload, 'storage')).toBe(upload)
    const blob = new Blob(['image'])
    expect(mapAssetPaths(blob, 'storage')).toBe(blob)
  })
})

it('normalizes pathname bases and rejects external or ambiguous bases', () => {
  expect(normalizeBase('/aicardhub')).toBe('/aicardhub/')
  expect(normalizeBase('')).toBe('/')
  for (const value of ['https://other.example/', '//other.example/', 'aicardhub', '/x/../y', '/x?y', '/x#y', '/x\\y'])
    expect(() => normalizeBase(value)).toThrow('VITE_BASE')
})
