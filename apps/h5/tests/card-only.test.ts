import type { PublicCard } from '../src/api/generated'
import { describe, expect, it } from 'vitest'
import { createSSRApp } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'
import { renderToString } from 'vue/server-renderer'
import DarkCardBody from '../src/components/visitor/DarkCardBody.vue'
import { cardOnlyRedirect } from '../src/router/card-only'

const page = { render: () => null }

function createTestRouter() {
  const router = createRouter({
    history: createMemoryHistory('/aicardhub/'),
    routes: [
      { path: '/card/:code', name: '/card/[code]', component: page },
      { path: '/chat/:code', name: '/chat/[code]', component: page },
      { path: '/staff/card', name: '/staff/card/', component: page },
      { path: '/staff/login', name: '/staff/login', component: page },
      { path: '/staff/assistant/test', name: '/staff/assistant/test', component: page },
      { path: '/:path(.*)', name: '/[...path]', component: page },
    ],
  })
  router.beforeEach(cardOnlyRedirect)
  return router
}

describe('card-only navigation', () => {
  it('keeps an encoded card code, supported attribution and optional lead form but discards the question', async () => {
    const router = createTestRouter()
    await router.push('/chat/a%2Fb?s=nfc&e=07&q=old&lead=1&other=secret#chat')
    expect(router.currentRoute.value.fullPath).toBe('/card/a%2Fb?s=nfc&e=7&lead=1')
  })

  it.each(['s=bogus&e=0&lead=yes', 's=nfc&s=qr&e=2&e=3&lead=1&lead=1', 'e=9007199254740993', 'e=1e3', 'e=7%0A'])(
    'keeps no invalid or repeated chat query values (%s)',
    async (query) => {
      const router = createTestRouter()
      await router.push(`/chat/card1?${query}`)
      expect(router.currentRoute.value.fullPath).toBe('/card/card1')
    },
  )

  it('removes only q from an existing card link', async () => {
    const router = createTestRouter()
    await router.push('/card/card1?s=poster&e=42&lead=1&q=one&q=two#contact')
    expect(router.currentRoute.value.fullPath).toBe('/card/card1?s=poster&e=42&lead=1#contact')
  })

  it.each(['/staff/assistant', '/staff/assistant/test', '/STAFF/assistant/old/child'])(
    'passes the staff card to auth instead of the blocked route (%s)',
    async (path) => {
      const router = createTestRouter()
      router.beforeEach(to => to.path === '/staff/login' ? undefined : { path: '/staff/login', query: { redirect: to.fullPath } })
      await router.push(path)
      expect(router.currentRoute.value.query.redirect).toBe('/staff/card')
    },
  )
})

describe('card-only presentation', () => {
  it.each([undefined, false])('keeps public products and contact entry with showAi=%s', async (showAi) => {
    const card: PublicCard = {
      code: 'card1', status: 'active', name: '示例员工', company: { name: '示例公司' },
      products: [{ id: 1, title: '公开产品', ask_question: '产品指引问题' }],
    }
    const output = await renderToString(createSSRApp(DarkCardBody, { card, showAi }))
    expect(output).toContain('公开产品')
    expect(output).toContain('留下联系方式')
    expect(output.includes('class="dk-prod-ask"')).toBe(showAi !== false)
    expect(output.includes('class="dk-entry"')).toBe(showAi !== false)
  })
})
