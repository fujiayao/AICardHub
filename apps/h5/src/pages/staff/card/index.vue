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
  const [card, today, week, visitors] = await Promise.all([
    getCard(),
    getStats({ query: { range: 'today' } }),
    getStats({ query: { range: '7d' } }),
    getVisitors({ query: { page: 1, page_size: 3 } }),
  ])
  return { card, today, week, visitors }
})
</script>

<template>
  <StaffShell title="我的名片">
    <ResourceState :loading="loading" :error="error" @retry="reload">
      <template v-if="data">
        <div class="banner banner-ai">
          <span class="icon i-lucide-smartphone" aria-hidden="true" />
          <span class="grow">把员工端添加到手机桌面，新线索一打开就能看到</span>
          <router-link class="banner-act" to="/staff/me?install=1">去设置</router-link>
        </div>
        <StaffCard :card="data.card" />
        <div class="card-ops">
          <van-button block to="/staff/card/edit"><span class="icon i-lucide-pencil" aria-hidden="true" />编辑名片</van-button>
          <van-button block :to="`/card/${data.card.code}`"><span class="icon i-lucide-eye" aria-hidden="true" />访客视角</van-button>
        </div>
        <div class="send-row">
          <van-button block type="primary" to="/staff/card/share"><span class="icon i-lucide-send" aria-hidden="true" />发送名片</van-button>
        </div>
        <StatsPanel :today="data.today" :week="data.week" />
        <div class="sec-title"><span>最近访客</span><router-link to="/staff/customers?tab=visitors">查看全部<span class="icon i-lucide-chevron-right" /></router-link></div>
        <div v-if="data.visitors.items.length" class="group">
          <router-link v-for="visitor in data.visitors.items" :key="visitor.id" class="vis-item" :to="`/staff/customers/${visitor.id}?kind=visitor`">
            <span class="avatar anon"><span class="icon i-lucide-user" /></span>
            <div class="vis-main">
              <div class="l1">访客 #{{ visitor.anon_id.slice(-4).toUpperCase() }}</div>
              <div class="l2">{{ dateLabel(visitor.last_seen_at) }}</div>
            </div>
            <span class="icon i-lucide-chevron-right vis-arrow" />
          </router-link>
        </div>
        <p v-else class="empty-inline">还没有访客，发送名片开启交流</p>
        <div class="banner nfc-strip">
          <span class="icon i-lucide-nfc nfc-ico" aria-hidden="true" />
          <span class="grow">NFC 功能未启用</span>
        </div>
      </template>
    </ResourceState>
  </StaffShell>
</template>

<style scoped>
.banner {
  margin: 0 0 14px;
  padding: 10px 12px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--fs-sm);
}
.banner .icon {
  width: 18px;
  height: 18px;
  flex: none;
}
.banner .grow {
  flex: 1;
}
.banner-ai {
  background: var(--c-ai-soft);
  color: var(--c-ai-ink);
}
.banner-act {
  font-weight: 600;
  color: var(--c-ai);
}
.card-ops {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 14px;
}
.card-ops .icon,
.send-row .icon {
  width: 18px;
  height: 18px;
  margin-right: 6px;
}
.send-row {
  padding-top: 10px;
}
.sec-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 0 10px;
  font-size: var(--fs-md);
  font-weight: 600;
  color: var(--c-ink);
}
.sec-title a {
  font-size: var(--fs-sm);
  font-weight: 400;
  color: var(--c-primary);
  display: flex;
  align-items: center;
  gap: 2px;
}
.sec-title a .icon {
  width: 16px;
  height: 16px;
}
.group {
  background: var(--c-surface);
  border-radius: var(--r-lg);
  overflow: hidden;
}
.vis-item {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px 16px;
  position: relative;
  color: var(--c-text);
}
.vis-item + .vis-item::before {
  content: "";
  position: absolute;
  top: 0;
  left: 60px;
  right: 0;
  height: 1px;
  background: var(--c-line);
}
.avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--r-pill);
  display: grid;
  place-items: center;
  flex: none;
}
.avatar.anon {
  background: var(--c-bg);
  color: var(--c-text-2);
}
.avatar .icon {
  width: 18px;
  height: 18px;
}
.vis-main {
  flex: 1;
  min-width: 0;
}
.vis-main .l1 {
  font-size: var(--fs-base);
  color: var(--c-text);
}
.vis-main .l2 {
  font-size: var(--fs-sm);
  color: var(--c-text-3);
  margin-top: 2px;
}
.vis-arrow {
  width: 16px;
  height: 16px;
  color: var(--c-text-3);
  flex: none;
}
.empty-inline {
  padding: 24px 0;
  text-align: center;
  color: var(--c-text-3);
  font-size: var(--fs-sm);
}
.nfc-strip {
  background: var(--c-surface);
  color: var(--c-text-2);
  margin: 16px 0;
}
.nfc-ico {
  color: var(--c-ai);
}
</style>
