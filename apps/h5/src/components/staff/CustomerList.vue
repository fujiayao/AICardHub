<script setup lang="ts">
import type { LeadData, VisitorData } from '@/api/generated'
import { computed, shallowRef, watch } from 'vue'
import { leads, visitors } from '@/api/generated'
import ResourceState from '@/components/common/ResourceState.vue'
import { usePaged } from '@/composables/usePaged'
import { dateLabel, leadStatuses, maskPhone, statusLabel } from '@/utils/format'
const props = defineProps<{ kind: 'leads' | 'visitors' }>()
const status = shallowRef(''); const search = shallowRef('')
const pager = usePaged<LeadData | VisitorData>(page => props.kind === 'leads' ? leads({ query: { page, page_size: 20, status: status.value || undefined, q: search.value || undefined } }) : visitors({ query: { page, page_size: 20 } }))
const { items, loading, refreshing, error, finished } = pager
watch([status, () => props.kind], () => pager.refresh())
const empty = computed(() => !loading.value && !error.value && !items.value.length)
function isLead(item: LeadData | VisitorData): item is LeadData { return 'phone' in item }
function overdue(item: LeadData) { return item.status === 'new' && Date.now() - new Date(item.created_at).getTime() > 86400000 }
</script>
<template><div class="stack"><template v-if="kind === 'leads'"><van-search v-model="search" aria-label="搜索客户" placeholder="搜索姓名、手机号" @search="pager.refresh" @clear="pager.refresh" /><div class="filters"><button :class="{ active: !status }" @click="status = ''">全部</button><button v-for="option in leadStatuses" :key="option.value" :class="{ active: status === option.value }" @click="status = option.value">{{ option.label }}</button></div></template><van-pull-refresh v-model="refreshing" @refresh="pager.refresh"><ResourceState :error="error" :empty="empty" :empty-text="kind === 'leads' ? '还没有线索' : '还没有访客'" @retry="pager.refresh"><van-list :loading="loading" :finished="finished" finished-text="已显示全部" :immediate-check="false" @load="pager.load()"><router-link v-for="item in items" :key="item.id" class="customer panel stack" :to="`/staff/customers/${item.id}${isLead(item) ? '' : '?kind=visitor'}`"><template v-if="isLead(item)"><div class="row between"><h2>{{ item.name }}</h2><span class="tag" :class="{ amber: item.status === 'new' }">{{ statusLabel(item.status) }}</span></div><p class="muted num">{{ maskPhone(item.phone) }}<span v-if="item.company_name"> · {{ item.company_name }}</span></p><p v-if="item.need" class="need">{{ item.need }}</p><p v-if="overdue(item)" class="notice">超时未跟进</p><p class="muted small">{{ dateLabel(item.created_at) }}</p></template><template v-else><h2>访客 #{{ item.anon_id.slice(-4) }}</h2><p class="muted">最近访问 {{ dateLabel(item.last_seen_at) }}</p></template></router-link></van-list></ResourceState><div v-if="loading" role="status" class="empty-inline"><van-loading size="20">正在加载</van-loading></div></van-pull-refresh></div></template>
<style scoped>.filters{display:flex;gap:8px;overflow-x:auto}.filters button{flex-shrink:0;min-height:44px;border:1px solid var(--c-line);border-radius:var(--r-pill);padding:0 12px;background:var(--c-surface);color:var(--c-text-2)}.filters button.active{background:var(--c-ink);color:var(--c-surface)}.customer{display:block;color:var(--c-text);margin-bottom:12px}.need{margin:8px 0;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.amber{color:var(--c-amber);background:var(--c-amber-soft)}</style>
