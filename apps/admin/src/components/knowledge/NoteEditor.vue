<script setup lang="ts">
import { reactive, useTemplateRef, watch } from "vue";
import { MdEditor, config } from "md-editor-v3";
import DOMPurify from "dompurify";
import "md-editor-v3/lib/style.css";
import type { FormInstance, FormRules } from "element-plus";
import type { Note } from "@/api/schema";
// The unused browser-fullscreen extension otherwise injects a CDN script on mount.
// Explicitly disable it; fullscreen is not exposed in this editor's toolbar.
config({
  editorExtensions: { screenfull: { instance: { isEnabled: false } } },
});
const props = defineProps<{
  initial: Pick<Note, "title" | "content" | "public" | "approved">;
  busy: boolean;
  draftOnly?: boolean;
}>();
const emit = defineEmits<{
  save: [value: Pick<Note, "title" | "content" | "public" | "approved">];
  dirty: [];
}>();
const model = reactive({
  title: props.initial.title,
  content: props.initial.content,
  public: props.initial.public,
  approved: props.initial.approved,
});
const form = useTemplateRef<FormInstance>("form");
const rules: FormRules = {
  title: [
    { required: true, message: "请填写知识标题" },
    { max: 200, message: "标题不能超过200字" },
  ],
  content: [{ required: true, message: "请填写 Markdown 正文" }],
};
watch(model, () => emit("dirty"), { deep: true });
async function save() {
  if (await form.value?.validate().catch(() => false))
    emit("save", {
      title: model.title,
      content: model.content,
      public: model.public,
      approved: model.approved,
    });
}
const sanitize = (html: string) => DOMPurify.sanitize(html);
</script>
<template>
  <el-form
    :disabled="busy"
    ref="form"
    :model="model"
    :rules="rules"
    label-position="top"
    @submit.prevent="save"
    ><el-form-item label="标题" prop="title"
      ><el-input v-model="model.title" maxlength="200" /></el-form-item
    ><el-form-item class="markdown-field" label="Markdown 内容" prop="content"
      ><MdEditor
        v-model="model.content"
        :sanitize="sanitize"
        :toolbars="[
          'bold',
          'italic',
          'title',
          'quote',
          'unorderedList',
          'orderedList',
          'codeRow',
          'code',
          'link',
          'table',
          'revoke',
          'next',
          'preview',
          'catalog',
        ]"
        :no-upload-img="true"
        :no-katex="true"
        :no-mermaid="true"
        :no-highlight="true"
        :no-prettier="true"
        :preview="false" /></el-form-item
    ><el-form-item v-if="!draftOnly" label="公开给访客"
      ><el-switch
        aria-label="公开给访客"
        v-model="model.public" /></el-form-item
    ><el-form-item v-if="!draftOnly" label="管理员批准"
      ><el-switch
        aria-label="管理员批准"
        v-model="model.approved" /></el-form-item
    ><el-alert
      title="只有同时公开并批准的版本才可用于访客回答。保存草稿不等于发布；撤回后立即停止用于检索。"
      type="warning"
      :closable="false"
      show-icon
    />
    <p>
      <el-button native-type="submit" type="primary" :loading="busy">{{
        model.public && model.approved ? "保存并发布" : "保存草稿"
      }}</el-button>
    </p></el-form
  >
</template>
