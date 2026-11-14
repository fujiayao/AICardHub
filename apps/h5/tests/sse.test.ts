import { describe, expect, it, vi } from 'vitest'
import { createEventParser, streamChat } from '../src/api/sse'
describe('sSE transport', () => {
 it('joins split CRLF packets and preserves Chinese UTF-8', () => {
  const onEvent = vi.fn(); const parser = createEventParser(onEvent)
  parser.feed('event: delta\r\ndata: {"text":"你'); parser.feed('好"}\r\n\r'); parser.feed('\n')
  expect(onEvent).toHaveBeenCalledExactlyOnceWith({ event: 'delta', data: { text: '你好' } })
 })
 it('parses glued events, comments, and a final event without trailing blank line', () => {
  const events: unknown[] = []; const parser = createEventParser(e => events.push(e))
  parser.feed(': heartbeat\n\nevent: delta\ndata: {"text":"甲"}\n\nevent: lead_prompt\ndata: {"reason":"主动留资","title":"进一步了解"}\n\nevent: done\ndata: {"message_id":1,"kb_refs":[],"nokb":false,"model":"fake"}')
  parser.finish(); expect(events).toHaveLength(3); expect(events[2]).toMatchObject({ event: 'done', data: { message_id: 1 } })
 })
 it('rejects malformed JSON instead of silently dropping it', () => {
  expect(() => createEventParser(vi.fn()).feed('event: delta\ndata: not-json\n\n')).toThrow('回答格式异常')
 })
 it('uses visitor Bearer rather than staff identity and handles byte splits', async () => {
  vi.stubGlobal('localStorage', { getItem: (key: string) => key.includes('visitor') ? 'visitor-token' : 'staff-token' })
  const bytes = new TextEncoder().encode('event: delta\ndata: {"text":"你好"}\n\n')
  const fetcher = vi.fn().mockResolvedValue(new Response(new ReadableStream({ start(c) { c.enqueue(bytes.slice(0, 31)); c.enqueue(bytes.slice(31)); c.close() } }), { status: 200 }))
  vi.stubGlobal('fetch', fetcher); const event = vi.fn(); const controller = new AbortController()
  await streamChat('/api/v1/public/chat/sessions/1/messages', '问题', 'visitor', controller.signal, event)
  expect(fetcher.mock.calls[0]?.[1].headers.Authorization).toBe('Bearer visitor-token')
  expect(fetcher.mock.calls[0]?.[1].signal).toBe(controller.signal)
  expect(event).toHaveBeenCalledWith({ event: 'delta', data: { text: '你好' } })
  vi.unstubAllGlobals()
 })
})
