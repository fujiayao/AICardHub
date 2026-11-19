import type { VisitorDetail } from '../src/api/generated'
import { describe, expect, it } from 'vitest'
import { createSSRApp, defineComponent, h } from 'vue'
import { renderToString } from 'vue/server-renderer'
import CustomerHistory from '../src/components/staff/CustomerHistory.vue'

async function render(visitor: VisitorDetail, showConversations?: boolean) {
  const app = createSSRApp(CustomerHistory, { visitor, showConversations })
  app.component('van-empty', defineComponent({ props: ['description'], render() { return h('p', this.description) } }))
  return renderToString(app)
}

describe('customer visit and conversation history', () => {
  it('renders the API source, exact stay duration, intent and escaped tags', async () => {
    const output = await render({
      id: 72, anon_id: 'synthetic-visitor', last_seen_at: '2026-11-14T08:00:00Z',
      visits: [{ source: 'nfc', created_at: '2026-11-14T08:00:00Z', stay_seconds: 137 }],
      sessions: [{ id: 19, summary: '接口返回的摘要', intent_level: 'A', tags: ['真实接口标签', '<script>不可执行</script>'], messages: [] }],
    })
    expect(output).toContain('NFC 碰一碰')
    expect(output).toContain('137')
    expect(output).toContain('A 高意向')
    expect(output).toContain('接口返回的摘要')
    expect(output).toContain('真实接口标签')
    expect(output).toContain('&lt;script&gt;不可执行&lt;/script&gt;')
    expect(output).not.toContain('<script>')
  })

  it('shows empty history without inventing visits or conversation attributes', async () => {
    const output = await render({ id: 72, anon_id: 'synthetic-visitor', last_seen_at: '2026-11-14T08:00:00Z', sessions: [] })
    expect(output).toContain('暂无访问记录')
    expect(output).toContain('该访客还没有对话')
    expect(output).not.toContain('高意向')
    expect(output).not.toContain('需求标签')
  })

  it('can preserve visits while suppressing historical conversations', async () => {
    const output = await render({
      id: 72, anon_id: 'synthetic-visitor', last_seen_at: '2026-11-14T08:00:00Z',
      visits: [{ source: 'qr', created_at: '2026-11-14T08:00:00Z', stay_seconds: 47 }],
      sessions: [{ id: 19, summary: '历史摘要', intent_level: 'A', tags: ['历史标签'], messages: [] }],
    }, false)
    expect(output).toContain('扫码')
    expect(output).toContain('47')
    expect(output).not.toMatch(/对话|历史摘要|历史标签|高意向/)
  })
})
