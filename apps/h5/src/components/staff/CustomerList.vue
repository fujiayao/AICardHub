<script setup lang="ts">
import type { LeadData, VisitorData } from '@/api/generated'
import { computed, shallowRef, watch } from 'vue'
import { leads, visitors } from '@/api/generated'
import ResourceState from '@/components/common/ResourceState.vue'
import { usePaged } from '@/composables/usePaged'
import { dateLabel, intentLevelLabels, leadStatuses, maskPhone, sourceLabel, statusLabel } from '@/utils/format'
const props = defineProps<{ kind: 'leads' | 'visitors' }>()
const status = shallowRef(''); const search = shallowRef('')
const pager = usePaged<LeadData | VisitorData>(page => props.kind === 'leads' ? leads({ query: { page, page_size: 20, status: status.value || undefined, q: search.value || undefined } }) : visitors({ query: { page, page_size: 20 } }))
const { items, loading, refreshing, error, finished } = pager
watch([status, () => props.kind], () => pager.refresh())
const empty = computed(() => !loading.value && !error.value && !items.value.length)
function isLead(item: LeadData | VisitorData): item is LeadData { return 'phone' in item }
function overdue(item: LeadData) { return item.status === 'new' && Date.now() - new Date(item.created_at).getTime() > 86400000 }
</script>
<template><div class="stack"><template v-if="kind === 'leads'"><van-search v-model="search" aria-label="搜索客户" placeholder="搜索姓名、手机号" @search="pager.refresh" @clear="pager.refresh" /><div class="filters"><button :class="{ active: !status }" @click="status = ''">全部</button><button v-for="option in leadStatuses" :key="option.value" :class="{ active: status === option.value }" @click="status = option.value">{{ option.label }}</button></div></template><van-pull-refresh v-model="refreshing" @refresh="pager.refresh"><ResourceState :error="error" :empty="empty" :empty-text="kind === 'leads' ? '还没有线索，发送名片开启交流' : '还没有访客'" @retry="pager.refresh"><van-list :loading="loading" :finished="finished" finished-text="已显示全部" :immediate-check="false" @load="pager.load()"><router-link v-for="item in items" :key="item.id" class="customer panel" :to="`/staff/customers/${item.id}${isLead(item) ? '' : '?kind=visitor'}`"><template v-if="isLead(item)"><div class="row between head"><h2>{{ item.name }}</h2><span class="status" :class="item.status">{{ statusLabel(item.status) }}</span></div><p class="meta num">{{ maskPhone(item.phone) }}<span v-if="item.company_name" class="company"> · {{ item.company_name }}</span></p><p v-if="item.need" class="need">{{ item.need }}</p><div class="row between foot"><span class="muted small">{{ [sourceLabel(item.source), dateLabel(item.created_at)].filter(Boolean).join('｜') }}</span><span v-if="overdue(item)" class="overdue"><span class="icon i-lucide-clock" aria-hidden="true" />超时未跟进</span></div></template><template v-else><div class="vis-row"><span class="avatar anon"><span class="icon i-lucide-user" aria-hidden="true" /></span><div class="vis-main"><div class="vis-l1">访客 #{{ item.anon_id.slice(-4).toUpperCase() }}<span v-if="item.source" class="tag tag-gray">{{ sourceLabel(item.source) }}</span></div><div class="vis-l2">最近访问 {{ dateLabel(item.last_seen_at) }}</div></div><div class="vis-side"><span v-if="item.intent_level" class="lv" :class="`lv-${item.intent_level}`" :aria-label="intentLevelLabels[item.intent_level]">{{ item.intent_level }}</span><span class="icon i-lucide-chevron-right chevron" aria-hidden="true" /></div></div></template></router-link></van-list></ResourceState><div v-if="loading" role="status" class="empty-inline"><van-loading size="20">正在加载</van-loading></div></van-pull-refresh></div></template>
<style scoped>
.filters{display:flex;gap:var(--sp-2);overflow-x:auto;padding-bottom:4px}
.filters button{flex-shrink:0;min-height:36px;border:1px solid var(--c-line);border-radius:var(--r-pill);padding:0 14px;background:var(--c-surface);color:var(--c-text-2);font-size:var(--fs-sm)}
.filters button.active{background:var(--c-ink);color:var(--c-surface);border-color:var(--c-ink)}
.customer{display:block;color:var(--c-text);margin-bottom:var(--sp-3)}
.head{align-items:center;gap:var(--sp-2)}
.head h2{min-width:0;overflow-wrap:anywhere}
.chevron{color:var(--c-text-3);flex-shrink:0}
.meta{font-size:var(--fs-sm);color:var(--c-text-2);margin-top:4px}
.meta .company{overflow-wrap:anywhere}
.status{flex-shrink:0;padding:2px 10px;border-radius:var(--r-sm);font-size:var(--fs-xs);background:var(--c-bg);color:var(--c-text-2)}
.status.new{background:var(--c-amber-soft);color:var(--c-amber)}
.status.contacted{background:var(--c-primary-soft);color:var(--c-primary)}
.status.converted{background:var(--c-success-soft);color:var(--c-success)}
.need{margin:var(--sp-2) 0;color:var(--c-text);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.foot{margin-top:var(--sp-2);align-items:center}
.overdue{display:inline-flex;align-items:center;gap:4px;color:var(--c-amber);font-size:var(--fs-xs)}
.vis-row{display:flex;align-items:center;gap:12px}
.vis-row .avatar{width:40px;height:40px;border-radius:var(--r-pill);display:grid;place-items:center;flex:none;background:var(--c-bg);color:var(--c-text-2)}
.vis-row .avatar .icon{width:18px;height:18px}
.vis-main{flex:1;min-width:0}
.vis-l1{display:flex;align-items:center;gap:6px;font-size:var(--fs-base);color:var(--c-text)}
.vis-l1 .tag-gray{background:var(--c-tag-gray-bg);color:var(--c-text-2)}
.vis-l2{font-size:var(--fs-sm);color:var(--c-text-3);margin-top:2px}
.vis-side{display:flex;align-items:center;gap:6px;flex:none}
.lv{width:22px;height:22px;border-radius:6px;display:inline-grid;place-items:center;font-size:12px;font-weight:700;font-family:var(--font-num)}
.lv-A{background:var(--c-amber);color:var(--c-surface)}
.lv-B{background:var(--c-primary-soft);color:var(--c-primary)}
.lv-C{background:var(--c-tag-gray-bg);color:var(--c-text-3)}
</style>
