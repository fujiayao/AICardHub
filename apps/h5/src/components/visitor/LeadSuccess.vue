<script setup lang="ts">
import { callPhone } from '@/platform'
import { maskPhone } from '@/utils/format'
defineProps<{ name: string, phone?: string | null, summary: { name: string, phone: string, company_name: string }, code: string, backQuery?: Record<string, string> }>()
defineEmits<{ continue: [] }>()
</script>

<template>
  <main class="page white">
    <div class="page-body result-body">
      <div class="result">
        <div class="ok"><span class="icon i-lucide-check" aria-hidden="true" /></div>
        <h2>已提交</h2>
        <p>{{ name }}会尽快与您联系<br>也可以继续和 AI 分身聊聊</p>
      </div>
      <div class="summary-box">
        <div><span>称呼</span><b>{{ summary.name || '—' }}</b></div>
        <div><span>手机</span><b class="num">{{ maskPhone(summary.phone) }}</b></div>
        <div><span>公司</span><b>{{ summary.company_name || '—' }}</b></div>
      </div>
      <div class="result-actions">
        <van-button block type="primary" @click="$emit('continue')">继续聊聊</van-button>
        <van-button block :to="{ path: `/card/${code}`, query: backQuery }">返回名片</van-button>
      </div>
      <p v-if="phone" class="call-hint">着急的话可以直接 <button class="call-link" @click="callPhone(phone)">致电 {{ phone }}</button></p>
    </div>
  </main>
</template>

<style scoped>
.result-body{background:var(--c-bg)}
.result{display:flex;flex-direction:column;align-items:center;text-align:center;padding:48px 28px 24px}
.ok{width:72px;height:72px;border-radius:var(--r-pill);background:var(--c-success-soft);color:var(--c-success);display:grid;place-items:center}
.ok .icon{width:36px;height:36px}
.result h2{margin:18px 0 6px;font-size:var(--fs-lg);color:var(--c-ink)}
.result p{margin:0;font-size:var(--fs-base);color:var(--c-text-2);line-height:1.7}
.summary-box{margin:24px 16px 0;padding:14px 16px;border-radius:var(--r-lg);background:var(--c-surface);font-size:var(--fs-sm);color:var(--c-text-2)}
.summary-box div{display:flex;justify-content:space-between;padding:4px 0}
.summary-box div b{color:var(--c-text);font-weight:500;overflow-wrap:anywhere;text-align:right;max-width:70%}
.result-actions{display:flex;flex-direction:column;gap:10px;padding:24px 16px 0}
.call-hint{text-align:center;margin-top:20px;font-size:var(--fs-xs);color:var(--c-text-3)}
.call-link{border:0;padding:0;background:transparent;color:var(--c-primary);cursor:pointer;font:inherit}
</style>
