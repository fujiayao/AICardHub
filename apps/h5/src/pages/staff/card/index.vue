<!-- 原型: B2 我的名片工作台 -->
<script setup lang="ts">
import { card as getCard, stats as getStats, visitors as getVisitors } from '@/api/generated'
import ResourceState from '@/components/common/ResourceState.vue'
import StaffCard from '@/components/staff/StaffCard.vue'
import StaffShell from '@/components/staff/StaffShell.vue'
import StatsPanel from '@/components/staff/StatsPanel.vue'
import { useResource } from '@/composables/useResource'
import { dateLabel } from '@/utils/format'
const { data, loading, error, reload } = useResource(async () => {
 const [card, stats, visitors] = await Promise.all([getCard(), getStats({ query: { range: '7d' } }), getVisitors({ query: { page: 1, page_size: 3 } })])
 return { card, stats, visitors }
})
</script>
<template><StaffShell title="我的名片"><ResourceState :loading="loading" :error="error" @retry="reload"><template v-if="data"><StaffCard :card="data.card" /><div class="row"><van-button block to="/staff/card/edit">编辑名片</van-button><van-button block :to="`/card/${data.card.code}`">访客视角</van-button></div><van-button block type="primary" to="/staff/card/share">发送名片</van-button><StatsPanel :stats="data.stats" /><section class="panel"><div class="row between"><h2>最近访客</h2><router-link to="/staff/customers?tab=visitors">查看全部</router-link></div><van-cell v-for="visitor in data.visitors.items" :key="visitor.id" :title="`访客 #${visitor.anon_id.slice(-4)}`" :label="dateLabel(visitor.last_seen_at)" is-link :to="`/staff/customers/${visitor.id}?kind=visitor`" /><p v-if="!data.visitors.items.length" class="empty-inline">还没有访客，发送名片开启交流</p></section><p class="muted small">NFC 实物管理暂未开放</p><van-cell title="添加到手机桌面" label="打开更方便，及时查看新消息" is-link to="/staff/me?install=1" /></template></ResourceState></StaffShell></template>
