import type { StreamEvent } from '../src/api/sse'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { effectScope } from 'vue'
import { useChatStream } from '../src/composables/useChatStream'
const transport = vi.hoisted(() => vi.fn())
vi.mock('../src/api/sse', () => ({ streamChat: transport }))
describe('chat state', () => {
 beforeEach(() => { transport.mockReset() })
 afterEach(() => vi.restoreAllMocks())
 it('keeps partial output on failure and forbids replay', async () => {
  transport.mockImplementation(async (_p, _q, _i, _s, event: (e: StreamEvent) => void) => { event({ event: 'delta', data: { text: '已收到部分回答' } }); throw new Error('断线') })
  const scope = effectScope(); const chat = scope.run(() => useChatStream(() => '/stream'))!
  await chat.send('问题'); expect(chat.messages.value[1]).toMatchObject({ content: '已收到部分回答', failed: true, interrupted: true })
  await chat.retry(); expect(transport).toHaveBeenCalledTimes(1); scope.stop()
 })
 it('caps lead prompts and never creates a lead from phone text', async () => {
  transport.mockImplementation(async (_p, _q, _i, _s, event: (e: StreamEvent) => void) => {
   for (let i = 0; i < 4; i++) event({ event: 'lead_prompt', data: { title: '联系', reason: '自愿' } })
   event({ event: 'done', data: { message_id: 2, kb_refs: [], nokb: false, model: 'fake' } })
  })
  const scope = effectScope(); const chat = scope.run(() => useChatStream(() => '/stream'))!
  await chat.send('我的手机号13800000000'); expect(chat.leadPrompts.value).toHaveLength(2); expect(chat.messages.value).toHaveLength(2); expect(chat.error.value).toBe(''); scope.stop()
 })
})
