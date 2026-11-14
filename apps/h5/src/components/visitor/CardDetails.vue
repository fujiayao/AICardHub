<script setup lang="ts">
import type { PublicCard } from '@/api/generated'
import { shallowRef } from 'vue'
import { copyText, openMap } from '@/platform'
defineProps<{ card: PublicCard }>()
const emit = defineEmits<{ question: [question: string] }>()
const expanded = shallowRef(false)
</script>

<template>
  <template v-if="card.mobile || card.email || card.company.address">
    <h2 class="sec-title">联系方式</h2>
    <div class="group contact">
      <div v-if="card.mobile" class="cell">
        <span class="cell-ico"><span class="icon i-lucide-phone" /></span>
        <div class="cell-main"><div class="cell-title num">{{ card.mobile }}</div><div class="cell-desc">手机</div></div>
        <button class="act" @click="copyText(card.mobile)"><span class="icon i-lucide-copy" />复制</button>
      </div>
      <div v-if="card.email" class="cell">
        <span class="cell-ico"><span class="icon i-lucide-mail" /></span>
        <div class="cell-main"><div class="cell-title">{{ card.email }}</div><div class="cell-desc">邮箱</div></div>
        <button class="act" @click="copyText(card.email)"><span class="icon i-lucide-copy" />复制</button>
      </div>
      <div v-if="card.company.address" class="cell">
        <span class="cell-ico"><span class="icon i-lucide-map-pin" /></span>
        <div class="cell-main"><div class="cell-title addr">{{ card.company.address }}</div><div class="cell-desc">地址</div></div>
        <button class="act" @click="card.company.address && openMap(card.company.address)"><span class="icon i-lucide-navigation" />导航</button>
      </div>
    </div>
  </template>

  <template v-if="card.intro">
    <h2 class="sec-title">关于我</h2>
    <div class="co-card intro-card">{{ card.intro }}</div>
  </template>

  <h2 class="sec-title">公司介绍</h2>
  <div class="co-card">
    <div class="co-head">
      <span class="co-logo"><img v-if="card.company.logo_url" :src="card.company.logo_url" alt="" width="22"><span v-else class="icon i-lucide-hexagon" /></span>
      <div class="co-head-text"><b>{{ card.company.name }}</b></div>
    </div>
    <p v-if="card.company.intro" class="co-intro" :class="{ collapsed: !expanded }">{{ card.company.intro }}</p>
    <p v-else class="co-intro muted">公司介绍由后台统一维护</p>
    <button v-if="card.company.intro" class="more-link" @click="expanded = !expanded">{{ expanded ? '收起' : '展开' }}</button>
  </div>

  <template v-if="card.products?.length">
    <h2 class="sec-title">主营业务<small>左右滑动</small></h2>
    <div class="prod-row">
      <article v-for="product in card.products" :key="product.id" class="prod">
        <div class="prod-img">
          <img v-if="product.image_url" :src="product.image_url" :alt="product.title">
          <span class="prod-title">{{ product.title }}</span>
        </div>
        <div class="prod-body">
          <p>{{ product.summary }}</p>
          <button v-if="product.ask_question" class="ask" @click="product.ask_question && emit('question', product.ask_question)"><span class="icon i-lucide-sparkles" />问问 AI</button>
        </div>
      </article>
    </div>
  </template>
</template>

<style scoped>
.sec-title{display:flex;align-items:center;justify-content:space-between;padding:20px 16px 10px;font-size:var(--fs-md);font-weight:600;color:var(--c-ink)}
.sec-title small{font-size:var(--fs-sm);font-weight:400;color:var(--c-text-3)}
.group{margin:0 16px;background:var(--c-surface);border-radius:var(--r-lg);overflow:hidden}
.cell{min-height:52px;display:flex;align-items:center;gap:12px;padding:12px 16px;position:relative}
.cell + .cell::before{content:"";position:absolute;top:0;left:16px;right:0;height:1px;background:var(--c-line)}
.cell-ico{width:34px;height:34px;border-radius:var(--r-md);display:grid;place-items:center;flex:none;background:var(--c-bg);color:var(--c-ink)}
.cell-ico .icon{width:18px;height:18px}
.cell-main{flex:1;min-width:0}
.cell-title{font-size:var(--fs-base);color:var(--c-text);overflow-wrap:anywhere}
.cell-title.addr{line-height:1.5}
.cell-desc{font-size:var(--fs-sm);color:var(--c-text-3);margin-top:2px}
.act{display:flex;align-items:center;gap:3px;border:0;padding:0;background:transparent;font-size:var(--fs-sm);color:var(--c-primary);cursor:pointer;flex:none}
.act .icon{width:16px;height:16px}
.co-card{margin:0 16px;background:var(--c-surface);border-radius:var(--r-lg);padding:16px}
.intro-card{font-size:var(--fs-base);color:var(--c-text-2);line-height:1.75}
.co-head{display:flex;align-items:center;gap:10px;min-width:0}
.co-logo{width:40px;height:40px;border-radius:var(--r-md);background:var(--c-ink);color:var(--c-surface);display:grid;place-items:center;flex:none}
.co-head-text{min-width:0}
.co-head-text b{display:block;color:var(--c-ink);font-size:var(--fs-base);overflow-wrap:anywhere;line-height:1.3}
.co-intro{margin-top:10px;font-size:var(--fs-sm);color:var(--c-text-2);line-height:1.7}
.co-intro.collapsed{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.more-link{margin-top:6px;border:0;padding:0;background:transparent;font-size:var(--fs-sm);color:var(--c-primary);cursor:pointer}
.prod-row{display:flex;gap:10px;overflow-x:auto;padding:0 16px 4px;scroll-snap-type:x mandatory;scroll-padding:0 16px}
.prod-row::-webkit-scrollbar{display:none}
.prod{flex:none;width:236px;border-radius:var(--r-lg);background:var(--c-surface);overflow:hidden;scroll-snap-align:start}
.prod-img{height:104px;position:relative;overflow:hidden;background:linear-gradient(135deg,var(--c-primary),var(--c-ink))}
.prod-img img{width:100%;height:100%;object-fit:cover}
.prod-title{position:absolute;left:12px;bottom:10px;color:var(--c-surface);font-weight:700;font-size:var(--fs-md);letter-spacing:.04em}
.prod-body{padding:10px 12px 12px}
.prod-body p{margin:0 0 8px;font-size:var(--fs-sm);color:var(--c-text-2);line-height:1.55;min-height:40px;overflow-wrap:anywhere}
.ask{display:inline-flex;align-items:center;gap:4px;border:0;padding:0;background:transparent;font-size:var(--fs-sm);font-weight:600;color:var(--c-ai);cursor:pointer}
.ask .icon{width:16px;height:16px}
</style>
