<!-- 原型: B13 消息中心 -->
<script setup lang="ts">
import type { NotificationData } from '@/api/generated'
import { computed, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { notifications, readAll, readNotification } from '@/api/generated'
import PageShell from '@/components/common/PageShell.vue'
import ResourceState from '@/components/common/ResourceState.vue'
import { useMutation } from '@/composables/useMutation'
import { usePaged } from '@/composables/usePaged'
import { useUnreadCount } from '@/composables/useUnreadCount'
import { dateLabel } from '@/utils/format'
import { notificationTarget } from '@/utils/notification-target'
const router = useRouter()
const unread = useUnreadCount(); const tab = shallowRef('all')
const pager = usePaged(page => notifications({ query: { page, page_size: 20 } }))
const { items, loading, refreshing, error, finished } = pager
const { saving, failure, run } = useMutation()
const visible = computed(() => tab.value === 'unread' ? items.value.filter(n => !n.read_at) : items.value)
const groups = computed(() => {
 const now = new Date(); const today = now.toLocaleDateString('zh-CN'); const yesterday = new Date(now.getTime() - 86400000).toLocaleDateString('zh-CN')
 const result = new Map<string, NotificationData[]>()
 for (const item of visible.value) { const date = new Date(item.created_at).toLocaleDateString('zh-CN'); const group = date === today ? '今天' : date === yesterday ? '昨天' : date; result.set(group, [...(result.get(group) || []), item]) }
 return [...result.entries()]
})
async function read(item: NotificationData) {
 const result = await run(async () => {
  if (!item.read_at) await readNotification({ path: { id: item.id } })
  return true
 })
 if (result) {
  item.read_at ||= new Date().toISOString()
  void unread.refresh()
  const target = notificationTarget(item)
  if (target) await router.push(target)
 }
}
async function markAll() { const result = await run(async () => { await readAll(); return true }); if (result) { await pager.refresh(); unread.refresh() } }
</script>
<template><PageShell title="消息中心" back><template #action><button class="text-button" :disabled="saving || !unread.count" @click="markAll">全部已读</button></template><van-tabs v-model:active="tab"><van-tab title="全部" name="all" /><van-tab :title="`未读（${unread.count}）`" name="unread" /></van-tabs><p v-if="failure" class="error" role="alert">{{ failure }}</p><van-pull-refresh v-model="refreshing" @refresh="pager.refresh"><ResourceState :error="error" :empty="!loading && !visible.length" empty-text="暂时没有消息" @retry="pager.refresh"><van-list :loading="loading" :finished="finished" :immediate-check="false" @load="pager.load()"><section v-for="[date, records] in groups" :key="date" class="stack group"><h2>{{ date }}</h2><button v-for="item in records" :key="item.id" class="panel notification" :aria-label="`${item.read_at ? '已读' : '未读'}消息：${item.title}`" @click="read(item)"><div class="row between"><h3>{{ item.title }}</h3><span v-if="!item.read_at" class="dot" aria-label="未读" /></div><p class="preline">{{ item.content }}</p><span class="muted small">{{ dateLabel(item.created_at) }}</span></button></section></van-list></ResourceState><van-loading v-if="loading" size="20">正在加载</van-loading></van-pull-refresh></PageShell></template>
<style scoped>.group{margin-bottom:20px}.notification{text-align:left;border:0;width:100%;color:var(--c-text)}.notification p{margin:8px 0;font-size:var(--fs-sm)}.dot{width:8px;height:8px;background:var(--c-danger);border-radius:var(--r-pill)}</style>
