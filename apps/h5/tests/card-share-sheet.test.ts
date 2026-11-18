import type { PublicCard } from '../src/api/generated'
import { Button, Loading, Popup } from 'vant'
import { afterEach, expect, it, vi } from 'vitest'
import { createSSRApp } from 'vue'
import { renderToString } from 'vue/server-renderer'
import CardShareSheet from '../src/components/visitor/CardShareSheet.vue'

vi.mock('../src/platform', () => ({
  copyText: vi.fn(), prepareShareImage: vi.fn(), share: vi.fn(), shareImage: vi.fn(),
}))
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs() })

it('renders a branded-image endpoint with campaign QR attribution and separate link actions', async () => {
  vi.stubGlobal('window', { location: { origin: 'https://cards.example' } })
  vi.stubEnv('BASE_URL', '/aicardhub/')
  const card: PublicCard = { code: 'synthetic', status: 'active', name: '合成姓名', company: { name: '合成企业' } }
  const app = createSSRApp(CardShareSheet, { modelValue: true, card, query: 's=link&e=7' })
  app.component('van-button', Button)
  app.component('van-popup', Popup)
  app.component('van-loading', Loading)
  const html = await renderToString(app)
  expect(html).toContain('https://cards.example/aicardhub/c/synthetic?s=poster&amp;e=7&amp;image=1&amp;v=0')
  expect(html).toContain('合成姓名的商务名片')
  expect(html).toContain('复制名片链接')
  expect(html).toContain('分享链接')
  expect(html).toContain('长按识别图中二维码')
  expect(html).not.toContain('发送名片图片')
})

it('does not render an image request while closed even when the popup keeps its slot mounted', async () => {
  vi.stubGlobal('window', { location: { origin: 'https://cards.example' } })
  const card: PublicCard = { code: 'synthetic', status: 'active', name: '合成姓名', company: { name: '合成企业' } }
  const app = createSSRApp(CardShareSheet, { modelValue: false, card, query: 's=link' })
  // An always-mounted slot mirrors Vant after its first opening; visibility alone is insufficient.
  app.component('van-popup', { template: '<div><slot /></div>' })
  app.component('van-button', Button)
  app.component('van-loading', Loading)
  const html = await renderToString(app)
  expect(html).toContain('分享名片')
  expect(html).not.toContain('<img')
  expect(html).not.toContain('image=1')
})
