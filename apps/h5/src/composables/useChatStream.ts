import { onScopeDispose, ref, shallowRef } from 'vue'
import { errorMessage } from '@/api/client'
import { streamChat } from '@/api/sse'
export interface ChatMessage { id: number, role: string, content: string, kb_refs: unknown[], failed?: boolean, interrupted?: boolean, feedback?: boolean }
export function useChatStream(getPath: () => string, staff = false) {
 const messages = ref<ChatMessage[]>([])
 const sending = shallowRef(false); const error = shallowRef(''); const model = shallowRef('')
 const leadPrompts = ref<{ title: string, reason: string }[]>([])
 let localId = -1
 let controller: AbortController | undefined
 let lastQuestion = ''; let completed = false
 async function send(question: string) {
  const content = question.trim(); if (!content || sending.value) return
  lastQuestion = content; error.value = ''; sending.value = true; completed = false
  messages.value.push({ id: localId--, role: 'user', content, kb_refs: [] })
  messages.value.push({ id: localId--, role: 'assistant', content: '', kb_refs: [] })
  const answer = messages.value[messages.value.length - 1]!
  controller = new AbortController()
  try {
   await streamChat(getPath(), content, staff ? 'staff' : 'visitor', controller.signal, (event) => {
    if (event.event === 'delta') answer.content += event.data.text
    if (event.event === 'lead_prompt' && !staff && leadPrompts.value.length < 2) leadPrompts.value.push(event.data)
    if (event.event === 'done') { answer.id = event.data.message_id; answer.kb_refs = event.data.kb_refs; model.value = event.data.model; completed = true }
    if (event.event === 'error') throw new Error(event.data.message)
   })
   if (!completed) throw new Error('连接中断，回答可能不完整')
  } catch (e) {
   if (controller.signal.aborted) { answer.interrupted = true; return }
   error.value = errorMessage(e); answer.failed = true; answer.interrupted = Boolean(answer.content)
  } finally { sending.value = false }
 }
 function retry() {
  const last = messages.value.at(-1)
  if (!last?.failed || last.interrupted) return
  messages.value.splice(-2, 2); return send(lastQuestion)
 }
 function stop() { controller?.abort() }
 onScopeDispose(stop)
 return { messages, sending, error, model, leadPrompts, send, retry, stop }
}
