<script setup lang="ts">
import { ref, shallowRef } from "vue";
import { ElMessage, type UploadFile, type UploadFiles } from "element-plus";
import { api } from "@/api/adapters";
import type { KnowledgeUploadRow, Note } from "@/api/schema";
import { useTask, confirmAction } from "@/composables/useTask";
import LoadState from "@/components/LoadState.vue";
import NoteEditor from "./NoteEditor.vue";
const emit = defineEmits<{ saved: [] }>();
const files = shallowRef<File[]>([]),
  rows = ref<KnowledgeUploadRow[]>([]),
  selected = shallowRef<number | null>(null),
  saved = ref<Record<number, string>>({});
const { busy, error, run } = useTask();
function select(_file: UploadFile, list: UploadFiles) {
  files.value = list.flatMap((item) => (item.raw ? [item.raw] : []));
}
async function parse() {
  if (!files.value.length) return;
  if (
    files.value.length > 20 ||
    files.value.some(
      (file) =>
        !file.name.toLowerCase().endsWith(".md") || file.size > 1024 * 1024,
    ) ||
    files.value.reduce((sum, file) => sum + file.size, 0) > 20 * 1024 * 1024
  ) {
    ElMessage.warning("每批1–20个.md文件，每篇不超过1MB、合计不超过20MB");
    return;
  }
  if (
    rows.value.length &&
    !(await confirmAction(
      "重新解析会丢弃尚未保存的上传预览，已保存的草稿不受影响。",
    ))
  )
    return;
  await run(async () => {
    rows.value = (await api.uploadKnowledge(files.value)).items;
    saved.value = {};
    selected.value = null;
  });
}
async function save(
  body: Pick<Note, "title" | "content" | "public" | "approved">,
) {
  const index = selected.value;
  if (index === null || saved.value[index]) return;
  if (
    !(await confirmAction(
      "仅将本篇内容保存为未发布草稿？上传文件的公开或批准标记不会生效。",
    ))
  )
    return;
  await run(async () => {
    const note = await api.saveNote(null, {
      title: body.title,
      content: body.content,
      public: false,
      approved: false,
    });
    if (note.public || note.approved)
      throw new Error("保存状态不符合未发布草稿要求，请立即核对");
    saved.value[index] = note.file_id;
    selected.value = null;
    emit("saved");
    ElMessage.success("本篇已保存为未发布草稿");
  });
}
</script>
<template>
  <section>
    <el-alert
      title="上传只解析，不保存、不发布。请逐篇预览并确认保存；公开审批必须回到知识列表单独操作。"
      type="info"
      :closable="false"
    />
    <p class="muted">
      每批1–20个UTF-8
      Markdown文件，每篇≤1MB、合计≤20MB。支持frontmatter标题/说明，后端逐篇校验；任何上传的public/approved字段均不能获得发布权限。
    </p>
    <el-upload
      multiple
      accept=".md"
      :auto-upload="false"
      :disabled="busy"
      :on-change="select"
      :on-remove="select"
      ><el-button>选择 Markdown 文件</el-button></el-upload
    >
    <p>
      <el-button
        type="primary"
        :loading="busy"
        :disabled="!files.length || busy"
        @click="parse"
        >解析并预览</el-button
      >
    </p>
    <LoadState :busy="busy" :error="error" @retry="parse" /><el-table
      :data="rows"
      empty-text="请选择文件后解析"
      ><el-table-column
        prop="filename"
        label="文件"
        min-width="170"
      /><el-table-column label="状态" width="100"
        ><template #default="{ row, $index }"
          ><el-tag
            :type="saved[$index] ? 'success' : row.valid ? 'warning' : 'danger'"
            >{{
              saved[$index] ? "已存草稿" : row.valid ? "待确认" : "无效"
            }}</el-tag
          ></template
        ></el-table-column
      ><el-table-column
        prop="message"
        label="校验说明"
        min-width="200"
      /><el-table-column label="操作" width="120"
        ><template #default="{ row, $index }"
          ><el-button
            link
            type="primary"
            :disabled="!row.valid || !!saved[$index] || busy"
            @click="selected = $index"
            >预览本篇</el-button
          ></template
        ></el-table-column
      ></el-table
    >
    <div
      v-if="selected !== null && rows[selected]?.draft"
      class="upload-preview"
    >
      <h2>{{ rows[selected].filename }}</h2>
      <NoteEditor
        :key="selected"
        :initial="{
          title: rows[selected].draft!.title,
          content: rows[selected].draft!.content,
          public: false,
          approved: false,
        }"
        :busy="busy"
        :draft-only="true"
        @save="save"
      />
    </div>
  </section>
</template>
<style scoped>
.upload-preview {
  margin-top: 24px;
}
</style>
