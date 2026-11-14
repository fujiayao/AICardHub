<!-- 原型: B5 AI 助手 -->
<script setup lang="ts">
import type { AssistantInput } from '@/api/generated'
import { showToast } from 'vant'
import { computed, nextTick, onMounted, shallowRef, watch } from 'vue'
import { assistant as getAssistant, assistantMetrics as getMetrics, templates as getTemplates, profile, saveAssistant } from '@/api/generated'
import DemoBadge from '@/components/common/DemoBadge.vue'
import ResourceState from '@/components/common/ResourceState.vue'
import AiStatusCard from '@/components/staff/AiStatusCard.vue'
import AssistantEditor from '@/components/staff/AssistantEditor.vue'
import StaffShell from '@/components/staff/StaffShell.vue'
import { useMutation } from '@/composables/useMutation'
import { useResource } from '@/composables/useResource'

const showTemplates = shallowRef(false)
const custom = shallowRef('')
// 当前正在编辑的字段；null = 全部只读展示，仅点「编辑」才挂载 AssistantEditor。
const editing = shallowRef<'persona_extra' | 'opening' | null>(null)
const personaExpanded = shallowRef(false)
const personaEl = shallowRef<HTMLElement>()
const personaOverflow = shallowRef(false)

const { data, loading, error, reload } = useResource(async () => {
  const [assistant, templates, staff, metrics] = await Promise.all([getAssistant(), getTemplates(), profile(), getMetrics()])
  return { assistant, templates, staff, metrics }
})
const { saving, failure, run } = useMutation()
const current = computed(() => data.value?.templates.find(t => t.id === data.value?.assistant.template_id))
const questions = computed(() => data.value?.assistant.guide_questions || [])
const suggestions = computed(() => (current.value?.guide_questions || []).filter(q => !questions.value.includes(q)))

// 待处理提醒：未命中与被点踩分别真实计数，不合并后统称「没答上来」。
const pendingText = computed(() => {
  const m = data.value?.metrics
  if (!m) return ''
  const parts: string[] = []
  if (m.unanswered > 0) parts.push(`${m.unanswered} 个问题没答上来`)
  if (m.disliked > 0) parts.push(`${m.disliked} 个回答被点踩`)
  return parts.length ? `${parts.join('，')}，去补充知识或纠错` : ''
})

function preview(value: string) {
  const staff = data.value?.staff
  return value
    .replaceAll('{姓名}', staff?.name || '')
    .replaceAll('{职位}', staff?.title || '')
    .replaceAll('{部门}', staff?.dept || '')
    .replaceAll('{负责业务}', staff?.business_scope || '')
}

// 人设正文保留完整原文存储；默认 3 行省略，溢出时才给「展开/收起」。
function checkOverflow() {
  if (personaExpanded.value) return
  const el = personaEl.value
  if (el) personaOverflow.value = el.scrollHeight - el.clientHeight > 1
}
watch(() => current.value?.persona, () => nextTick(checkOverflow))
onMounted(() => nextTick(checkOverflow))

async function save(part: Partial<AssistantInput>): Promise<boolean> {
  if (!data.value) return false
  const result = await run(() => saveAssistant({ body: { ...data.value!.assistant, ...part } }))
  if (result) {
    data.value = { ...data.value, assistant: result }
    showTemplates.value = false
    showToast('已保存')
    return true
  }
  return false
}

async function saveField(field: 'persona_extra' | 'opening', text: string) {
  if (await save({ [field]: text }))
    editing.value = null
}

function addQuestion() {
  if (!custom.value.trim() || questions.value.length >= 3)
    return
  void save({ guide_questions: [...questions.value, custom.value.trim()] })
  custom.value = ''
}
</script>

<template>
  <StaffShell title="AI 助手">
    <template #action>
      <van-button size="small" class="ai-button" to="/staff/assistant/test">试聊</van-button>
    </template>
    <ResourceState :loading="loading" :error="error" @retry="reload">
      <template v-if="data">
        <AiStatusCard :template-name="current?.name" :metrics="data.metrics" />
        <router-link v-if="pendingText" class="banner banner-amber" to="/staff/assistant/test">
          <span class="icon i-lucide-alert-circle" aria-hidden="true" />
          <span class="grow">{{ pendingText }}</span>
          <span class="icon i-lucide-chevron-right" aria-hidden="true" />
        </router-link>
        <DemoBadge />
        <p v-if="failure" class="error" role="alert">{{ failure }}</p>

        <!-- 人设模板 + 个人补充：同一白块，虚线分隔 -->
        <section class="block">
          <div class="block-h">
            <b><span class="icon i-lucide-user" aria-hidden="true" />人设</b>
            <div class="acts">
              <span role="button" tabindex="0" @click="showTemplates = true" @keyup.enter="showTemplates = true">
                <span class="icon i-lucide-arrow-left-right" aria-hidden="true" />切换模板
              </span>
            </div>
          </div>
          <span class="tpl-pill">
            <span class="icon i-lucide-layers" aria-hidden="true" />{{ current?.name || '尚未选择模板' }}
            <span v-if="current" class="tag tag-gray">公司模板</span>
          </span>
          <p ref="personaEl" class="txt preline" :class="{ clamp: !personaExpanded }">
            {{ current ? preview(current.persona || '') : '选择管理员提供的模板' }}
          </p>
          <button v-if="personaOverflow || personaExpanded" class="link-sm" @click="personaExpanded = !personaExpanded">
            {{ personaExpanded ? '收起' : '展开' }}
          </button>

          <div class="sub">
            <div class="block-h sub-h">
              <span class="hint">个人补充</span>
              <div v-if="editing !== 'persona_extra'" class="acts">
                <span role="button" tabindex="0" @click="editing = 'persona_extra'" @keyup.enter="editing = 'persona_extra'">
                  <span class="icon i-lucide-pencil" aria-hidden="true" />编辑
                </span>
              </div>
            </div>
            <template v-if="editing === 'persona_extra'">
              <AssistantEditor
                title="个人补充" field="persona_extra" :value="data.assistant.persona_extra || ''"
                :saving="saving" @save="saveField('persona_extra', $event)"
              />
              <button class="link-sm" @click="editing = null">取消</button>
            </template>
            <p v-else class="txt body preline">
              {{ data.assistant.persona_extra ? preview(data.assistant.persona_extra) : '补充你负责的业务、擅长的方向，让 AI 分身更贴近你' }}
            </p>
          </div>
        </section>

        <!-- 开场白 -->
        <section class="block">
          <div class="block-h">
            <b><span class="icon i-lucide-message-square" aria-hidden="true" />开场白</b>
            <div v-if="editing !== 'opening'" class="acts">
              <span role="button" tabindex="0" @click="editing = 'opening'" @keyup.enter="editing = 'opening'">
                <span class="icon i-lucide-pencil" aria-hidden="true" />编辑
              </span>
            </div>
          </div>
          <template v-if="editing === 'opening'">
            <AssistantEditor
              title="开场白" field="opening" :value="data.assistant.opening || ''"
              :saving="saving" @save="saveField('opening', $event)"
            />
            <button class="link-sm" @click="editing = null">取消</button>
          </template>
          <p v-else class="txt body preline">
            {{ data.assistant.opening ? preview(data.assistant.opening) : '写一句打招呼的话，访客进来第一眼就能看到' }}
          </p>
        </section>

        <!-- 引导问题 -->
        <section class="block">
          <div class="block-h">
            <b><span class="icon i-lucide-help-circle" aria-hidden="true" />引导问题<span class="hint weak">已选 {{ questions.length }}/3</span></b>
          </div>
          <div class="q-list">
            <div v-for="(question, index) in questions" :key="question" class="q-item">
              <span class="check on"><span class="icon i-lucide-check" aria-hidden="true" /></span>
              <span class="grow">{{ question }}</span>
              <button class="icon-button" :aria-label="`删除引导问题${index + 1}`" :disabled="saving" @click="save({ guide_questions: questions.filter((_, i) => i !== index) })">
                <span class="icon i-lucide-x" aria-hidden="true" />
              </button>
            </div>
            <button
              v-for="question in suggestions" :key="question" class="q-item off"
              :disabled="questions.length >= 3 || saving"
              @click="save({ guide_questions: [...questions, question] })"
            >
              <span class="check" aria-hidden="true" />
              <span class="grow">{{ question }}</span>
            </button>
          </div>
          <van-field v-model="custom" class="add-field" label="新增问题" maxlength="20" placeholder="最多 20 字">
            <template #button>
              <van-button size="small" :disabled="questions.length >= 3 || !custom.trim() || saving" @click="addQuestion">添加</van-button>
            </template>
          </van-field>
        </section>

        <!-- 知识与纠错 -->
        <div class="sec-title">知识与纠错</div>
        <van-cell-group inset>
          <van-cell title="个人知识" label="你负责的业务、案例、常见问题" :value="`${data.metrics.notes} 篇`" is-link to="/staff/assistant/notes" />
          <van-cell title="纠错记录" label="优先级最高，与其他知识冲突时以此为准" :value="`${data.metrics.corrections} 条`" is-link to="/staff/assistant/corrections" />
        </van-cell-group>
        <p class="muted small foot">公司介绍、产品资料等公司知识由管理员统一维护，自动生效，无需设置。个人知识和纠错是否可用于访客回答，以管理员批准为准。</p>

        <van-popup v-model:show="showTemplates" position="bottom" round closeable>
          <section class="sheet stack">
            <h2>选择模板</h2>
            <van-empty v-if="!data.templates.length" description="管理员尚未配置模板" />
            <button v-for="template in data.templates" :key="template.id" class="template-option" :disabled="saving" @click="save({ template_id: template.id })">
              <h3>{{ template.name }}</h3>
              <p class="muted preline">{{ preview(template.persona || '') }}</p>
            </button>
          </section>
        </van-popup>
      </template>
    </ResourceState>
  </StaffShell>
</template>

<style scoped>
.ai-button{background:var(--c-ai);color:var(--c-surface);border-color:var(--c-ai)}
.banner{display:flex;align-items:center;gap:8px;margin:12px 0 0;padding:10px 12px;border-radius:12px;font-size:var(--fs-sm)}
.banner .icon{width:18px;height:18px;flex:none}
.banner .grow{flex:1}
.banner-amber{background:var(--c-amber-soft);color:var(--c-amber-ink)}

.block{margin:12px 0 0;background:var(--c-surface);border-radius:var(--r-lg);padding:14px 16px}
.block-h{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}
.block-h b{font-size:var(--fs-base);color:var(--c-ink);display:flex;align-items:center;gap:6px}
.block-h b .icon{width:18px;height:18px}
.block-h .acts{display:flex;gap:14px;font-size:var(--fs-sm);color:var(--c-primary)}
.block-h .acts span[role="button"]{display:flex;align-items:center;gap:3px;cursor:pointer}
.block-h .acts .icon{width:16px;height:16px}
.hint{color:var(--c-text-3);font-size:var(--fs-sm)}
.hint.weak{font-weight:400;margin-left:6px}

.tpl-pill{display:inline-flex;align-items:center;gap:6px;padding:5px 10px;border-radius:8px;background:var(--c-bg);font-size:var(--fs-sm);color:var(--c-ink);margin-bottom:8px}
.tpl-pill .icon{width:16px;height:16px}
.tag-gray{background:var(--c-bg);color:var(--c-text-3);border:1px solid var(--c-line)}

.txt{margin:0;font-size:var(--fs-sm);color:var(--c-text-2);line-height:1.7}
.txt.body{color:var(--c-text)}
.txt.clamp{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:3;line-clamp:3;overflow:hidden}
.link-sm{margin-top:6px;background:none;border:0;padding:0;color:var(--c-primary);font-size:var(--fs-sm)}

.sub{margin-top:12px;padding-top:12px;border-top:1px dashed var(--c-line)}
.sub-h{margin-bottom:6px}

.q-list{display:flex;flex-direction:column;gap:8px;margin-bottom:4px}
.q-item{display:flex;align-items:center;gap:10px;font-size:var(--fs-sm);color:var(--c-text);background:none;border:0;padding:0;text-align:left;width:100%}
.q-item .grow{flex:1}
.q-item.off{color:var(--c-text-3);cursor:pointer}
.q-item.off:disabled{opacity:.5;cursor:default}
.check{width:18px;height:18px;border-radius:5px;border:1.5px solid var(--c-line);display:grid;place-items:center;flex:none;color:var(--c-surface)}
.check.on{background:var(--c-primary);border-color:var(--c-primary)}
.check .icon{width:12px;height:12px}
.icon-button{background:none;border:0;padding:2px;color:var(--c-text-3);display:grid;place-items:center}
.icon-button .icon{width:16px;height:16px}
.add-field{margin-top:8px;padding:0;--van-cell-background:transparent}

.sec-title{margin:18px 4px 8px;font-size:var(--fs-sm);color:var(--c-text-3)}
.foot{margin:12px 4px 20px;color:var(--c-text-3)}

.template-option{padding:16px;text-align:left;border:1px solid var(--c-line);border-radius:var(--r-md);background:var(--c-surface)}

/* 编辑态内联挂载 AssistantEditor：抹平其自带 panel，融入当前白块 */
.sub :deep(.panel),.block > :deep(.panel){padding:0;margin:0;background:transparent}
</style>
