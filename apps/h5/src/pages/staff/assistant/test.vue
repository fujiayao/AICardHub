<!-- 原型: B9 试聊调试 -->
<script setup lang="ts">
import type { ChatMessage } from '@/composables/useChatStream'
import { showToast } from 'vant'
import { shallowRef } from 'vue'
import { testSession } from '@/api/generated'
import ChatComposer from '@/components/common/ChatComposer.vue'
import ChatConversation from '@/components/common/ChatConversation.vue'
import DemoBadge from '@/components/common/DemoBadge.vue'
import PageShell from '@/components/common/PageShell.vue'
import ResourceState from '@/components/common/ResourceState.vue'
import CorrectionSheet from '@/components/staff/CorrectionSheet.vue'
import { useChatStream } from '@/composables/useChatStream'
import { useResource } from '@/composables/useResource'
const sessionId = shallowRef<number>(); const selected = shallowRef<ChatMessage>(); const question = shallowRef(''); const correcting = shallowRef(false)
const stream = useChatStream(() => `/api/v1/me/test-chat/sessions/${sessionId.value}/messages`, true)
const { messages, sending, model, error: streamError } = stream
const { data, loading, error, reload } = useResource(async () => { stream.stop(); const session = await testSession({ body: {} }); sessionId.value = session.session_id; messages.value = []; return session })
function correct(message: ChatMessage) { selected.value = message; const index = messages.value.indexOf(message); question.value = messages.value.slice(0, index).reverse().find(m => m.role === 'user')?.content || ''; correcting.value = true }
function saved() { messages.value.push({ id: -Date.now(), role: 'system', content: '纠错已保存，再问一次试试。', kb_refs: [] }) }
</script>
<template><PageShell title="试聊" back><template #action><button class="text-button" :disabled="sending || loading" @click="reload">清空</button></template><p class="ai-hint">调试对话不计入客户数据</p><DemoBadge :model="model" /><ResourceState :loading="loading" :error="error" @retry="reload"><section v-if="!messages.length" class="panel stack"><h2>试试我的 AI 分身</h2><p>{{ data?.opening }}</p><van-button v-for="item in data?.guide_questions" :key="item" plain @click="stream.send(item)">{{ item }}</van-button></section><ChatConversation :messages="messages" :sending="sending" staff @correction="correct" @retry="stream.retry" @feedback="showToast('试聊请使用纠错保存正确答案')" /><p v-if="streamError" class="error" role="alert">{{ streamError }}</p></ResourceState><template #footer><ChatComposer :sending="sending" :disabled="!sessionId || loading" @send="stream.send" @stop="stream.stop" /></template><CorrectionSheet v-model="correcting" :question="question" :wrong-answer="selected?.content" :message-id="selected && selected.id > 0 ? selected.id : undefined" source="test" @saved="saved" /></PageShell></template>
