import type { Identity } from './tokens'
import { ApiError } from './client'
import { clearToken, getToken } from './tokens'
export type StreamEvent =
 | { event: 'delta', data: { text: string } }
 | { event: 'lead_prompt', data: { reason: string, title: string } }
 | { event: 'done', data: { message_id: number, kb_refs: unknown[], nokb: boolean, model: string } }
 | { event: 'error', data: { code: string, message: string } }
export function createEventParser(onEvent: (event: StreamEvent) => void) {
 let pending = ''
 function feed(text: string) {
  pending += text
  let separator: RegExpExecArray | null
  while (true) {
   separator = /\r?\n\r?\n/.exec(pending)
   if (!separator) break
   const block = pending.slice(0, separator.index)
   pending = pending.slice(separator.index + separator[0].length)
   let event = 'message'; const data: string[] = []
   for (const line of block.split(/\r?\n/)) {
    if (line.startsWith('event:')) event = line.slice(6).trim()
    if (line.startsWith('data:')) data.push(line.slice(5).replace(/^ /, ''))
   }
   if (!data.length) continue
   let value: unknown
   try { value = JSON.parse(data.join('\n')) } catch { throw new ApiError('INVALID_SSE', '回答格式异常，请重新发起对话') }
   if (!value || typeof value !== 'object') throw new ApiError('INVALID_SSE', '回答格式异常')
   const v = value as Record<string, unknown>
   if (event === 'delta' && typeof v.text === 'string') onEvent({ event, data: { text: v.text } })
   else if (event === 'lead_prompt' && typeof v.title === 'string' && typeof v.reason === 'string') onEvent({ event, data: { title: v.title, reason: v.reason } })
   else if (event === 'done' && typeof v.message_id === 'number' && Array.isArray(v.kb_refs) && typeof v.model === 'string' && typeof v.nokb === 'boolean') onEvent({ event, data: { message_id: v.message_id, kb_refs: v.kb_refs, model: v.model, nokb: v.nokb } })
   else if (event === 'error' && typeof v.code === 'string' && typeof v.message === 'string') onEvent({ event, data: { code: v.code, message: v.message } })
  }
 }
 return { feed, finish() { if (pending.trim()) feed('\n\n') } }
}
export async function streamChat(path: string, content: string, identity: Exclude<Identity, 'public'>, signal: AbortSignal, onEvent: (event: StreamEvent) => void) {
 const response = await fetch(path, { method: 'POST', signal, headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken(identity)}`, Accept: 'text/event-stream' }, body: JSON.stringify({ content }) })
 if (!response.ok) {
  if (response.status === 401) { clearToken(identity); if (identity === 'staff') window.dispatchEvent(new Event('staff-session-expired')) }
  const error = await response.json().catch(() => ({})) as { code?: string, message?: string }
  throw new ApiError(error.code || 'STREAM_ERROR', error.message || '连接失败，请重试', response.status)
 }
 if (!response.body) throw new ApiError('EMPTY_STREAM', '服务没有返回回答流')
 const reader = response.body.getReader(); const decoder = new TextDecoder()
 const parser = createEventParser(onEvent)
 try { while (true) { const chunk = await reader.read(); if (chunk.done) break; parser.feed(decoder.decode(chunk.value, { stream: true })) }; parser.feed(decoder.decode()); parser.finish() }
 finally { reader.releaseLock() }
}
