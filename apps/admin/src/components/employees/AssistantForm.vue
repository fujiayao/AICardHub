<script setup lang="ts">
import { reactive, useTemplateRef } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import type { Assistant, Template } from "@/api/schema";
const props = defineProps<{
  initial: Assistant;
  templates: Template[];
  busy: boolean;
}>();
const emit = defineEmits<{ save: [value: Assistant] }>();
const model = reactive({
  ...props.initial,
  questions: (props.initial.guide_questions ?? []).join("\n"),
});
const form = useTemplateRef<FormInstance>("form");
const rules: FormRules = {
  opening: [{ required: true, message: "请填写开场白" }],
  questions: [
    {
      validator: (_r: unknown, v: string, cb: (e?: Error) => void) =>
        cb(
          v.split("\n").filter((q) => q.trim()).length > 3
            ? new Error("最多3个引导问题")
            : undefined,
        ),
    },
  ],
};
async function save() {
  if (await form.value?.validate().catch(() => false))
    emit("save", {
      template_id: model.template_id,
      persona_extra: model.persona_extra,
      opening: model.opening,
      guide_questions: model.questions
        .split("\n")
        .map((q) => q.trim())
        .filter(Boolean),
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
    ><el-form-item label="人设模板"
      ><el-select v-model="model.template_id" clearable
        ><el-option
          v-for="t in templates"
          :key="t.id"
          :label="t.name"
          :value="t.id"
          :disabled="!t.enabled" /></el-select></el-form-item
    ><el-form-item label="个人补充人设"
      ><el-input
        v-model="model.persona_extra"
        type="textarea"
        :rows="6"
        maxlength="300" /></el-form-item
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
        :rows="5"
        maxlength="2000" /></el-form-item
    ><el-button native-type="submit" type="primary" :loading="busy"
      >保存助手</el-button
    ></el-form
  >
</template>
