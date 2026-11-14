<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { api } from "@/api/adapters";
import type { Card, Assistant, Template } from "@/api/schema";
import FieldForm, { type Field } from "@/components/FieldForm.vue";
import { useTask } from "@/composables/useTask";
import LoadState from "@/components/LoadState.vue";
import AssistantForm from "./AssistantForm.vue";
const props = defineProps<{ code: string }>();
const card = ref<Card>(),
  assistant = ref<Assistant>(),
  templates = ref<Template[]>([]);
const { busy, error, run } = useTask();
const fields: Field[] = [
  { key: "display_title", label: "展示职务" },
  { key: "mobile", label: "联系电话", required: true, type: "phone" },
  { key: "email", label: "电子邮箱", type: "email" },
  { key: "intro", label: "个人简介", type: "textarea", max: 150 },
  { key: "photo_url", label: "职业照地址", type: "url" },
  { key: "photo_bg_url", label: "聊天背景地址", type: "url" },
  { key: "wechat_qr_url", label: "微信二维码地址", type: "url" },
];
async function load() {
  await run(async () => {
    const result = await Promise.all([
      api.card(props.code),
      api.assistant(props.code),
      api.templates(),
    ]);
    card.value = {
      ...result[0],
      display_title: result[0].display_title ?? result[0].title ?? "",
    };
    assistant.value = result[1];
    templates.value = result[2];
  });
}
function update(key: string, value: unknown) {
  if (card.value) card.value = { ...card.value, [key]: value };
}
async function save() {
  await run(async () => {
    if (!card.value) return;
    const {
      display_title,
      mobile,
      email,
      intro,
      photo_url,
      photo_bg_url,
      wechat_qr_url,
    } = card.value;
    card.value = await api.saveCard(props.code, {
      display_title,
      mobile,
      email,
      intro,
      photo_url,
      photo_bg_url,
      wechat_qr_url,
    });
    ElMessage.success("名片已保存");
  });
}
async function saveAssistant(body: Assistant) {
  await run(async () => {
    assistant.value = await api.saveAssistant(props.code, body);
    ElMessage.success("助手已保存");
  });
}
onMounted(load);
</script>
<template>
  <p class="muted">名片编号：{{ code }}。修改会影响访客看到的内容。</p>
  <LoadState :busy="busy" :error="error" @retry="load" /><el-tabs
    v-if="card && assistant"
    ><el-tab-pane label="个人名片"
      ><FieldForm
        :model="{ ...card }"
        :fields="fields"
        :busy="busy"
        @update="update"
        @submit="save" /></el-tab-pane
    ><el-tab-pane label="AI 助手"
      ><AssistantForm
        :initial="assistant"
        :templates="templates"
        :busy="busy"
        @save="saveAssistant" /></el-tab-pane
  ></el-tabs>
</template>
