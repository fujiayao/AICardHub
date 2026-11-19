<script setup lang="ts">
// 原型: A1 名片首页业务区（AI 入口 + 联系方式/个人简介/公司介绍/主营业务）。暗色，仅用 .vc-dark 注入的 --dk-* 变量。
// 首页职责：展示真实公开信息 + 引导进入对话；本组件绝不创建会话、不渲染消息流/输入框聊天。
import type { PublicCard } from '@/api/generated'
import { computed, shallowRef } from 'vue'
import { copyText, openMap } from '@/platform'

const props = withDefaults(defineProps<{ card: PublicCard, showAi?: boolean }>(), { showAi: true })
const emit = defineEmits<{ ask: [question: string], openChat: [], openLead: [] }>()

const expanded = shallowRef(false)
const opening = computed(() => props.card.assistant?.opening || '')
const questions = computed(() => props.card.assistant?.guide_questions || [])
const hasContact = computed(() => Boolean(props.card.mobile || props.card.email || props.card.company.address))
const products = computed(() => props.card.products || [])
const brandName = computed(() => props.card.company.short_name || props.card.company.name)
</script>

<template>
  <section class="dk-body">
    <!-- 联系方式：访客无需问 AI 即可查看/复制/导航 -->
    <template v-if="hasContact">
      <h2 class="dk-sec">联系方式</h2>
      <div class="dk-group">
        <div v-if="card.mobile" class="dk-cell">
          <span class="dk-cell-ico"><span class="icon i-lucide-phone" /></span>
          <div class="dk-cell-main"><div class="dk-cell-t">{{ card.mobile }}</div><div class="dk-cell-d">手机</div></div>
          <button class="dk-cell-act" @click="copyText(card.mobile)"><span class="icon i-lucide-copy" />复制</button>
        </div>
        <div v-if="card.email" class="dk-cell">
          <span class="dk-cell-ico"><span class="icon i-lucide-mail" /></span>
          <div class="dk-cell-main"><div class="dk-cell-t">{{ card.email }}</div><div class="dk-cell-d">邮箱</div></div>
          <button class="dk-cell-act" @click="copyText(card.email)"><span class="icon i-lucide-copy" />复制</button>
        </div>
        <div v-if="card.company.address" class="dk-cell">
          <span class="dk-cell-ico"><span class="icon i-lucide-map-pin" /></span>
          <div class="dk-cell-main"><div class="dk-cell-t addr">{{ card.company.address }}</div><div class="dk-cell-d">地址</div></div>
          <button class="dk-cell-act" @click="card.company.address && openMap(card.company.address)"><span class="icon i-lucide-navigation" />导航</button>
        </div>
      </div>
    </template>

    <!-- 个人简介：无内容整块不显示（不编造） -->
    <template v-if="card.intro">
      <h2 class="dk-sec">个人简介</h2>
      <div class="dk-card dk-intro">{{ card.intro }}</div>
    </template>

    <!-- 公司介绍：3 行折叠 + 展开 -->
    <h2 class="dk-sec">公司介绍</h2>
    <div class="dk-card">
      <div class="dk-co-head">
        <span class="dk-co-logo"><img v-if="card.company.logo_url" :src="card.company.logo_url" alt="" width="22"><span v-else class="icon i-lucide-hexagon" /></span>
        <div class="dk-co-name"><b>{{ card.company.name }}</b></div>
      </div>
      <p v-if="card.company.intro" class="dk-co-intro" :class="{ clamp: !expanded }">{{ card.company.intro }}</p>
      <p v-else class="dk-co-intro muted">公司介绍未公开</p>
      <button v-if="card.company.intro" class="dk-more" @click="expanded = !expanded">{{ expanded ? '收起' : '展开' }}</button>
    </div>

    <!-- 主营业务：真实产品卡，问问 AI 带问题进对话 -->
    <template v-if="products.length">
      <h2 class="dk-sec">主营业务<small>左右滑动</small></h2>
      <div class="dk-prod-row">
        <article v-for="product in products" :key="product.id" class="dk-prod">
          <div class="dk-prod-img">
            <img v-if="product.image_url" :src="product.image_url" :alt="product.title">
            <span class="dk-prod-title">{{ product.title }}</span>
          </div>
          <div class="dk-prod-body">
            <p>{{ product.summary }}</p>
            <button v-if="showAi && product.ask_question" class="dk-prod-ask" @click="product.ask_question && emit('ask', product.ask_question)"><span class="icon i-lucide-sparkles" />问问 AI</button>
          </div>
        </article>
      </div>
    </template>

    <!-- AI 入口放在全部公开信息之后：开场白 + 引导问题 + 进入对话（点击才进 /chat，首页不建会话） -->
    <div v-if="showAi" class="dk-entry">
      <div class="dk-entry-head">
        <span class="dk-entry-mark"><span class="icon i-lucide-sparkles" /></span>
        <div class="dk-entry-text">
          <b>{{ card.name ? `${card.name}的 AI 助手` : 'AI 助手' }}</b>
          <span>业务咨询与合作对接</span>
        </div>
        <span class="dk-entry-badge"><span class="dk-entry-dot" />AI 可用</span>
      </div>
      <p v-if="opening" class="dk-entry-say">{{ opening }}</p>
      <div v-if="questions.length" class="dk-entry-qs">
        <button v-for="question in questions" :key="question" class="dk-entry-q" @click="emit('ask', question)">
          <span class="dk-entry-q-text">{{ question }}</span>
          <span class="icon i-lucide-chevron-right" />
        </button>
      </div>
      <button class="dk-entry-ask" @click="emit('openChat')">
        <span>想了解业务、合作方向，或联系名片本人？</span>
        <i class="dk-entry-send"><span class="icon i-lucide-arrow-up" /></i>
      </button>
    </div>

    <p class="dk-foot">内容由{{ brandName }}官方维护<br>有合作意向？<button class="dk-foot-link" @click="emit('openLead')">留下联系方式</button>，供工作人员联系与需求跟进</p>
  </section>
</template>

<style scoped>
.dk-body { display: flex; flex-direction: column; padding-bottom: 92px; }
.dk-entry { margin: 22px 16px 0; padding: 16px; border-radius: 16px; background: linear-gradient(150deg, var(--dk-surface-2), var(--dk-surface)); border: 1px solid var(--dk-line-strong); }
.dk-entry-head { display: flex; align-items: center; gap: 10px; }
.dk-entry-mark { width: 32px; height: 32px; border-radius: 10px; flex: none; background: linear-gradient(145deg, var(--dk-mark-0), var(--dk-mark-1)); border: 1px solid var(--dk-avatar-ring); display: grid; place-items: center; }
.dk-entry-mark .icon { width: 16px; height: 16px; color: var(--dk-mint); }
.dk-entry-text { min-width: 0; flex: 1; }
.dk-entry-text b { display: block; font-size: 13.5px; font-weight: 600; color: var(--dk-txt); }
.dk-entry-text span { display: block; font-size: 10.5px; color: var(--dk-expo); margin-top: 2px; }
.dk-entry-badge { display: flex; align-items: center; gap: 5px; font-size: 10px; color: var(--dk-mint); flex: none; }
.dk-entry-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--dk-mint); }
.dk-entry-say { margin-top: 12px; font-size: 13px; line-height: 1.7; color: var(--dk-bubble-ai); background: var(--dk-surface-2); border: 1px solid var(--dk-line); border-radius: 5px 14px 14px; padding: 11px 14px; }
.dk-entry-qs { margin-top: 12px; display: flex; flex-direction: column; gap: 8px; }
.dk-entry-q { display: flex; align-items: center; gap: 10px; width: 100%; text-align: left; min-height: 44px; padding: 11px 14px; border-radius: 12px; cursor: pointer; background: var(--dk-surface-soft); border: 1px solid var(--dk-line-strong); color: var(--dk-tag); }
.dk-entry-q-text { flex: 1; min-width: 0; font-size: 13px; }
.dk-entry-q .icon { width: 16px; height: 16px; flex: none; color: var(--dk-expo); }
.dk-entry-ask { display: flex; align-items: center; gap: 8px; width: 100%; margin-top: 12px; padding: 5px 5px 5px 16px; border-radius: 22px; cursor: pointer; background: var(--dk-surface); border: 1px solid var(--dk-line-strong); }
.dk-entry-ask span { flex: 1; min-width: 0; text-align: left; font-size: 13px; color: var(--dk-placeholder); }
.dk-entry-send { width: 33px; height: 33px; border-radius: 50%; flex: none; background: var(--dk-mint); display: grid; place-items: center; color: var(--dk-on-mint); }
.dk-entry-send .icon { width: 16px; height: 16px; }

.dk-sec { display: flex; align-items: center; justify-content: space-between; padding: 22px 16px 10px; font-size: 14px; font-weight: 600; color: var(--dk-txt); }
.dk-sec small { font-size: 11px; font-weight: 400; color: var(--dk-expo); }
.dk-group { margin: 0 16px; background: var(--dk-surface); border: 1px solid var(--dk-line); border-radius: 14px; overflow: hidden; }
.dk-cell { min-height: 52px; display: flex; align-items: center; gap: 12px; padding: 12px 16px; position: relative; }
.dk-cell + .dk-cell::before { content: ""; position: absolute; top: 0; left: 16px; right: 0; height: 1px; background: var(--dk-line); }
.dk-cell-ico { width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center; flex: none; background: var(--dk-surface-soft); color: var(--dk-mint); }
.dk-cell-ico .icon { width: 18px; height: 18px; }
.dk-cell-main { flex: 1; min-width: 0; }
.dk-cell-t { font-size: 14px; color: var(--dk-txt); overflow-wrap: anywhere; }
.dk-cell-t.addr { line-height: 1.5; }
.dk-cell-d { font-size: 11px; color: var(--dk-expo); margin-top: 2px; }
.dk-cell-act { display: flex; align-items: center; gap: 3px; border: 0; padding: 0; background: transparent; font-size: 11.5px; color: var(--dk-mint); cursor: pointer; flex: none; }
.dk-cell-act .icon { width: 16px; height: 16px; }

.dk-card { margin: 0 16px; background: var(--dk-surface); border: 1px solid var(--dk-line); border-radius: 14px; padding: 16px; }
.dk-intro { font-size: 13px; color: var(--dk-tag); line-height: 1.75; }
.dk-co-head { display: flex; align-items: center; gap: 10px; min-width: 0; }
.dk-co-logo { width: 40px; height: 40px; border-radius: 10px; background: linear-gradient(140deg, var(--dk-mint), var(--dk-mint-deep)); color: var(--dk-on-mint); display: grid; place-items: center; flex: none; overflow: hidden; }
.dk-co-logo .icon { width: 20px; height: 20px; }
.dk-co-name { min-width: 0; }
.dk-co-name b { display: block; color: var(--dk-txt); font-size: 14px; overflow-wrap: anywhere; line-height: 1.3; }
.dk-co-intro { margin-top: 10px; font-size: 12.5px; color: var(--dk-tag); line-height: 1.7; }
.dk-co-intro.clamp { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.dk-co-intro.muted { color: var(--dk-expo); }
.dk-more { margin-top: 6px; border: 0; padding: 0; background: transparent; font-size: 12.5px; color: var(--dk-mint); cursor: pointer; }

.dk-prod-row { display: flex; gap: 10px; overflow-x: auto; padding: 0 16px 4px; scroll-snap-type: x mandatory; scrollbar-width: none; }
.dk-prod-row::-webkit-scrollbar { display: none; }
.dk-prod { flex: none; width: 236px; border-radius: 14px; background: var(--dk-surface); border: 1px solid var(--dk-line); overflow: hidden; scroll-snap-align: start; }
.dk-prod-img { height: 104px; position: relative; overflow: hidden; background: linear-gradient(135deg, var(--dk-mint-deep), var(--dk-surface-2)); }
.dk-prod-img img { width: 100%; height: 100%; object-fit: cover; }
.dk-prod-title { position: absolute; left: 12px; bottom: 10px; color: var(--dk-txt); font-weight: 700; font-size: 14px; letter-spacing: .04em; }
.dk-prod-body { padding: 10px 12px 12px; }
.dk-prod-body p { margin: 0 0 8px; font-size: 12px; color: var(--dk-tag); line-height: 1.55; min-height: 40px; overflow-wrap: anywhere; }
.dk-prod-ask { display: inline-flex; align-items: center; gap: 4px; border: 0; padding: 0; background: transparent; font-size: 12px; font-weight: 600; color: var(--dk-mint); cursor: pointer; }
.dk-prod-ask .icon { width: 16px; height: 16px; }

.dk-foot { text-align: center; font-size: 11px; color: var(--dk-expo); padding: 26px 24px 8px; line-height: 1.9; }
.dk-foot-link { border: 0; padding: 0; background: transparent; color: var(--dk-mint); font-size: 11px; cursor: pointer; text-decoration: underline; text-underline-offset: 3px; }
</style>
