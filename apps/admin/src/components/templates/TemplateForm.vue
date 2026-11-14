<script setup lang="ts">
import { reactive, useTemplateRef } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import type { Template } from "@/api/schema";
const props = defineProps<{ initial: Omit<Template, "id">; busy: boolean }>();
const emit = defineEmits<{ save: [value: Omit<Template, "id">] }>();
const model = reactive({
  ...props.initial,
  questions: (props.initial.guide_questions ?? []).join("\n"),
});
const form = useTemplateRef<FormInstance>("form");
const rules: FormRules = {
  name: [{ required: true, message: "请输入模板名称" }],
  persona: [{ required: true, message: "请输入人设" }],
  opening: [{ required: true, message: "请输入开场白" }],
  questions: [
    {
      validator: (_r: unknown, v: string, cb: (e?: Error) => void) =>
        cb(
          v.split("\n").filter((s) => s.trim()).length > 6
            ? new Error("最多6个引导问题")
            : undefined,
        ),
    },
  ],
};
async function save() {
  if (await form.value?.validate().catch(() => false))
    emit("save", {
      name: model.name,
      persona: model.persona,
      opening: model.opening,
      guide_questions: model.questions
        .split("\n")
        .map((q) => q.trim())
        .filter(Boolean),
      enabled: model.enabled,
      is_default: model.is_default,
    });
}
</script>
<template>
  <el-form
    ref="form"
    :model="model"
    :rules="rules"
    label-position="top"
    @submit.prevent="save"
    ><el-form-item label="模板名称" prop="name"
      ><el-input v-model="model.name" maxlength="100" /></el-form-item
    ><el-form-item label="人设" prop="persona"
      ><el-input
        v-model="model.persona"
        type="textarea"
        :rows="6"
        maxlength="10000" /></el-form-item
    ><el-form-item label="开场白" prop="opening"
      ><el-input
        v-model="model.opening"
        type="textarea"
        :rows="3"
        maxlength="2000" /></el-form-item
    ><el-form-item label="引导问题（每行一个）" prop="questions"
      ><el-input
        v-model="model.questions"
        type="textarea"
        :rows="4"
        maxlength="2000" /></el-form-item
    ><el-form-item label="启用"
      ><el-switch v-model="model.enabled" /></el-form-item
    ><el-button native-type="submit" type="primary" :loading="busy"
      >保存模板</el-button
    ></el-form
  >
</template>
