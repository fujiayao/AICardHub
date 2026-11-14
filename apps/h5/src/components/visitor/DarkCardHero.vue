<script setup lang="ts">
// 原型: 名片原型-demo.html 封面区（深绿-黑 / 薄荷）。仅访客使用，暗色变量由 .vc-dark 包裹层注入。
import type { PublicCard } from '@/api/generated'
import { computed } from 'vue'
import AnonymousPortrait from '@/components/common/AnonymousPortrait.vue'

const props = defineProps<{ card: PublicCard, hasWechat: boolean }>()
const emit = defineEmits<{ contact: [], call: [], wechat: [], share: [] }>()

const brandName = computed(() => props.card.company.short_name || props.card.company.name)
const initial = computed(() => (props.card.name || '').trim().slice(0, 1))
const role = computed(() => [props.card.dept, props.card.title].filter(Boolean).join(' · '))

function splitScope(value?: string | null): string[] {
  if (!value) return []
  return value.split(/[，,、/|\s]+/).map(s => s.trim()).filter(Boolean)
}
// 标签来自真实公开信息：业务范围 + 产品标题，去重，最多 6 个；无则不渲染。
const tags = computed(() => {
  const scope = splitScope(props.card.business_scope)
  const products = (props.card.products || []).map(p => p.title).filter(Boolean)
  return [...new Set([...scope, ...products])].slice(0, 6)
})

const expo = computed(() => {
  const c = props.card.campaign
  if (!c) return ''
  return [c.name, c.location, c.booth ? `展位 ${c.booth}` : ''].filter(Boolean).join(' · ')
})
</script>

<template>
  <section class="dk-hero">
    <div class="dk-brand">
      <span class="dk-logo"><img v-if="card.company.logo_url" :src="card.company.logo_url" alt="" width="14"><span v-else>{{ brandName.slice(0, 1) }}</span></span>
      <span class="dk-brand-name">{{ brandName }}</span>
      <button class="dk-share" aria-label="分享名片" @click="emit('share')"><span class="icon i-lucide-share-2" /></button>
    </div>

    <div class="dk-person">
      <span class="dk-avatar">
        <img v-if="card.photo_url" :src="card.photo_url" :alt="`${card.name}的职业照`">
        <span v-else-if="initial" class="dk-initial">{{ initial }}</span>
        <AnonymousPortrait v-else />
      </span>
      <div class="dk-person-text">
        <h1 class="dk-name">{{ card.name || '数科名片' }}</h1>
        <p v-if="role" class="dk-role">{{ role }}</p>
        <p v-if="card.business_scope" class="dk-org">{{ card.business_scope }}</p>
      </div>
    </div>

    <div v-if="tags.length" class="dk-tags">
      <span v-for="tag in tags" :key="tag" class="dk-tag">{{ tag }}</span>
    </div>

    <div class="dk-actions">
      <button class="dk-act" @click="emit('contact')">
        <span class="icon i-lucide-contact-round" /><span>存通讯录</span>
      </button>
      <button v-if="card.mobile" class="dk-act" @click="emit('call')">
        <span class="icon i-lucide-phone" /><span>电话</span>
      </button>
      <button v-if="hasWechat" class="dk-act" @click="emit('wechat')">
        <span class="icon i-lucide-message-circle" /><span>加微信</span>
      </button>
    </div>

    <p v-if="expo" class="dk-expo"><span class="dk-dot" />{{ expo }}</p>
  </section>
</template>

<style scoped>
.dk-hero {
  padding: 14px 22px 26px;
  position: relative;
  background:
    radial-gradient(ellipse 120% 80% at 15% 0%, var(--dk-hero-glow-a), transparent 60%),
    radial-gradient(ellipse 90% 70% at 95% 15%, var(--dk-hero-glow-b), transparent 65%);
}
.dk-brand { display: flex; align-items: center; gap: 8px; margin-bottom: 24px; }
.dk-logo {
  width: 22px; height: 22px; border-radius: 6px; flex: none;
  background: linear-gradient(140deg, var(--dk-mint), var(--dk-mint-deep));
  display: grid; place-items: center;
  font-size: 11px; font-weight: 800; color: var(--dk-on-mint);
}
.dk-brand-name { font-size: 12.5px; letter-spacing: .12em; color: var(--dk-brand); font-weight: 600; }
.dk-share {
  margin-left: auto; width: 32px; height: 32px; border: 0; border-radius: 50%;
  background: var(--dk-surface-soft); color: var(--dk-mint); display: grid; place-items: center; cursor: pointer;
}
.dk-share .icon { width: 16px; height: 16px; }

.dk-person { display: flex; gap: 16px; align-items: center; min-width: 0; }
.dk-person-text { min-width: 0; flex: 1; }
.dk-avatar {
  width: 72px; height: 72px; border-radius: 50%; flex: none; overflow: hidden;
  background: linear-gradient(150deg, var(--dk-avatar-0), var(--dk-avatar-1));
  border: 1.5px solid var(--dk-avatar-ring);
  display: grid; place-items: center;
  box-shadow: 0 0 0 4px var(--dk-avatar-halo), 0 8px 24px var(--dk-shadow);
}
.dk-avatar img { width: 100%; height: 100%; object-fit: cover; object-position: center top; }
.dk-initial { font-size: 28px; font-weight: 600; color: var(--dk-initial); }
.dk-name { font-size: 25px; font-weight: 650; letter-spacing: .02em; line-height: 1.2; color: var(--dk-txt); overflow-wrap: anywhere; }
.dk-role { font-size: 13px; color: var(--dk-role); margin-top: 5px; line-height: 1.5; overflow-wrap: anywhere; }
.dk-org { font-size: 12px; color: var(--dk-mint); margin-top: 3px; opacity: .9; overflow-wrap: anywhere; }

.dk-tags { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 20px; }
.dk-tag {
  font-size: 11.5px; padding: 4px 11px; border-radius: 20px;
  background: var(--dk-surface-soft); border: 1px solid var(--dk-line-strong);
  color: var(--dk-tag); letter-spacing: .02em;
}

.dk-actions { display: flex; gap: 10px; margin-top: 22px; }
.dk-act {
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: 7px;
  padding: 13px 0 11px; border-radius: 14px; cursor: pointer;
  background: var(--dk-surface-soft); border: 1px solid var(--dk-line-strong);
  transition: .18s; color: var(--dk-act-label);
}
.dk-act:active { transform: scale(.97); background: var(--dk-mint-dim); }
.dk-act .icon { width: 19px; height: 19px; color: var(--dk-mint); }
.dk-act span { font-size: 11px; }

.dk-expo { margin-top: 18px; display: flex; align-items: center; gap: 8px; font-size: 11px; color: var(--dk-expo); }
.dk-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--dk-mint); box-shadow: 0 0 8px var(--dk-mint); flex: none; }
</style>
