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
// 图标分类来自真实 target_type，与原型 B13 的类别一一对应；未知类型回落为系统铃铛。
const categories: Record<string, { icon: string, cls: string }> = {
 lead: { icon: 'i-lucide-user-plus', cls: 'cat-lead' },
 intent: { icon: 'i-lucide-zap', cls: 'cat-intent' },
 digest: { icon: 'i-lucide-bar-chart-2', cls: 'cat-digest' },
 issue: { icon: 'i-lucide-check', cls: 'cat-issue' },
}
function category(item: NotificationData) { return categories[item.target_type || ''] || { icon: 'i-lucide-bell', cls: 'cat-sys' } }
</script>
<template><PageShell title="消息中心" back><template #action><button class="text-button" :disabled="saving || !unread.count" @click="markAll">全部已读</button></template><van-tabs v-model:active="tab"><van-tab title="全部" name="all" /><van-tab :title="`未读（${unread.count}）`" name="unread" /></van-tabs><p v-if="failure" class="error" role="alert">{{ failure }}</p><van-pull-refresh v-model="refreshing" @refresh="pager.refresh"><ResourceState :error="error" :empty="!loading && !visible.length" empty-text="暂时没有消息" @retry="pager.refresh"><van-list :loading="loading" :finished="finished" :immediate-check="false" @load="pager.load()"><section v-for="[date, records] in groups" :key="date" class="group"><h2 class="day">{{ date }}</h2><div class="noti-card"><button v-for="item in records" :key="item.id" class="noti" :class="{ read: item.read_at }" :aria-label="`${item.read_at ? '已读' : '未读'}消息：${item.title}`" @click="read(item)"><span class="ic" :class="category(item).cls"><span class="icon" :class="category(item).icon" aria-hidden="true" /></span><div class="main"><div class="l1"><b>{{ item.title }}</b><span v-if="!item.read_at" class="dot" aria-label="未读" /><span class="t">{{ dateLabel(item.created_at) }}</span></div><p class="preline body">{{ item.content }}</p></div></button></div></section></van-list></ResourceState><van-loading v-if="loading" size="20">正在加载</van-loading></van-pull-refresh></PageShell></template>
<style scoped>
.group{margin-bottom:var(--sp-4)}
.day{padding:14px 4px 6px;font-size:var(--fs-xs);color:var(--c-text-3);font-weight:400}
.noti-card{background:var(--c-surface);border-radius:var(--r-lg);overflow:hidden}
.noti{display:flex;gap:12px;padding:14px 16px;position:relative;width:100%;text-align:left;border:0;background:transparent;color:var(--c-text)}
.noti + .noti::before{content:"";position:absolute;top:0;left:62px;right:0;height:1px;background:var(--c-line)}
.ic{width:36px;height:36px;border-radius:12px;display:grid;place-items:center;flex:none}
.ic .icon{width:18px;height:18px}
.cat-lead{background:var(--c-amber-soft);color:var(--c-amber-ink)}
.cat-intent{background:var(--c-amber-soft);color:var(--c-amber-ink)}
.cat-digest{background:var(--c-primary-soft);color:var(--c-primary)}
.cat-issue{background:var(--c-ai-soft);color:var(--c-ai)}
.cat-sys{background:var(--c-bg);color:var(--c-text-2)}
.main{flex:1;min-width:0}
.l1{display:flex;align-items:center;gap:6px}
.l1 b{font-size:var(--fs-base);color:var(--c-text);font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.noti.read .l1 b{font-weight:400;color:var(--c-text-2)}
.dot{flex-shrink:0;width:8px;height:8px;background:var(--c-danger);border-radius:var(--r-pill)}
.l1 .t{margin-left:auto;font-size:11px;color:var(--c-text-3);flex-shrink:0}
.body{margin:3px 0 0;font-size:var(--fs-sm);color:var(--c-text-3);line-height:1.55}
</style>
