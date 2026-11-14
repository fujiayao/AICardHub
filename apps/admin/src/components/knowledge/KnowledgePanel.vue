<script setup lang="ts">
import { ref, shallowRef, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { api } from "@/api/adapters";
import type { Note } from "@/api/schema";
import { usePage } from "@/composables/usePage";
import { useTask, confirmAction } from "@/composables/useTask";
import LoadState from "@/components/LoadState.vue";
import NoteEditor from "./NoteEditor.vue";
import KnowledgeUpload from "./KnowledgeUpload.vue";
import HistoryPanel from "./HistoryPanel.vue";
const { data, page, busy, error, load } = usePage((p) =>
  api.notes({ page: p, page_size: 20 }),
);
const editTask = useTask();
const selected = ref<Note | null>(null),
  draft = ref<Pick<Note, "title" | "content" | "public" | "approved"> | null>(
    null,
  ),
  historyId = shallowRef(""),
  editorKey = shallowRef(0);
const dirty = shallowRef(false);
const uploading = shallowRef(false);
async function switchAllowed() {
  return !dirty.value || (await confirmAction("编辑内容尚未保存，放弃修改？"));
}
async function create() {
  if (!(await switchAllowed())) return;
  selected.value = null;
  draft.value = { title: "", content: "", public: false, approved: false };
  editorKey.value++;
  dirty.value = false;
}
async function edit(row: Note) {
  if (!(await switchAllowed())) return;
  await editTask.run(async () => {
    const note = await api.note(row.file_id);
    selected.value = note;
    draft.value = {
      title: note.title,
      content: note.content,
      public: note.public,
      approved: note.approved,
    };
    editorKey.value++;
    dirty.value = false;
  });
}
async function save(
  body: Pick<Note, "title" | "content" | "public" | "approved">,
) {
  if (
    body.public &&
    body.approved &&
    !(await confirmAction(
      "确认该资料已获批准并允许在其所属知识范围内向访客公开？保存后即可被回答引用。",
    ))
  )
    return;
  await editTask.run(async () => {
    const note = await api.saveNote(selected.value?.file_id ?? null, body);
    selected.value = note;
    draft.value = { ...note };
    editorKey.value++;
    dirty.value = false;
    ElMessage.success(
      note.public && note.approved ? "知识已发布" : "草稿已保存",
    );
    await load();
  });
}
async function withdraw(row: Note) {
  if (!(await confirmAction(`撤回“${row.title}”？后端将立即停止检索该文件。`)))
    return;
  await editTask.run(async () => {
    const note = await api.note(row.file_id);
    await api.saveNote(row.file_id, {
      title: note.title,
      content: note.content,
      public: false,
      approved: false,
    });
    if (selected.value?.file_id === row.file_id) {
      selected.value = null;
      draft.value = null;
      dirty.value = false;
    }
    await load();
    ElMessage.success("知识已撤回");
  });
}
async function remove(row: Note) {
  if (!(await confirmAction(`删除“${row.title}”？该文件将退出知识库。`)))
    return;
  await editTask.run(async () => {
    await api.deleteNote(row.file_id);
    if (selected.value?.file_id === row.file_id) {
      selected.value = null;
      draft.value = null;
      dirty.value = false;
    }
    await load();
  });
}
async function openHistory(row: Note) {
  if (await switchAllowed()) {
    dirty.value = false;
    historyId.value = row.file_id;
  }
}
async function restored() {
  historyId.value = "";
  selected.value = null;
  draft.value = null;
  dirty.value = false;
  await load();
  ElMessage.success("正文已恢复为未发布草稿，请重新审核批准后发布");
}
onMounted(() => load());
</script>
<template>
  <section class="page">
    <div>
      <h1>公开知识</h1>
      <p class="muted">
        先审核内容，再公开发布。个人笔记保留所属名片范围，只有公开且批准后才可用于该名片的访客回答。
      </p>
    </div>
    <div class="panel">
      <div class="toolbar">
        <el-button type="primary" @click="create">新建 Markdown</el-button
        ><el-button @click="uploading = true">批量上传 Markdown</el-button
        ><el-button :loading="busy" @click="load()">刷新列表</el-button>
      </div>
      <LoadState
        :busy="busy"
        :error="error || editTask.error.value"
        @retry="load()"
      /><el-table :data="data.items" empty-text="尚无知识，请创建 Markdown 草稿"
        ><el-table-column
          prop="title"
          label="标题"
          min-width="180"
        /><el-table-column label="范围"
          ><template #default="{ row }"
            ><el-tag :type="row.scope === 'card' ? 'warning' : 'info'">{{
              row.scope === "card" ? "个人笔记" : "公司知识"
            }}</el-tag>
            <div v-if="row.scope === 'card'" class="muted">
              名片 {{ row.card_code }}
            </div></template
          ></el-table-column
        ><el-table-column prop="revision" label="版本" /><el-table-column
          label="状态"
          width="120"
          ><template #default="{ row }"
            ><el-tag :type="row.public && row.approved ? 'success' : 'info'">{{
              row.public && row.approved ? "已发布" : "未发布"
            }}</el-tag></template
          ></el-table-column
        ><el-table-column label="操作" min-width="260"
          ><template #default="{ row }"
            ><el-button
              link
              type="primary"
              :disabled="editTask.busy.value"
              @click="edit(row)"
              >编辑 / 审批</el-button
            ><el-button link type="primary" @click="openHistory(row)"
              >历史</el-button
            ><el-button
              link
              type="warning"
              :disabled="!row.public || editTask.busy.value"
              @click="withdraw(row)"
              >撤回</el-button
            ><el-button
              link
              type="danger"
              :disabled="editTask.busy.value"
              @click="remove(row)"
              >删除</el-button
            ></template
          ></el-table-column
        ></el-table
      ><el-pagination
        v-model:current-page="page"
        :total="data.total"
        :page-size="20"
        layout="prev,pager,next,total"
        @current-change="load"
      />
    </div>
    <div v-if="draft" class="panel">
      <h2>{{ selected ? "编辑知识" : "新建草稿" }}</h2>
      <p class="muted">
        {{ selected?.file_id ?? "保存后由服务器创建公司知识编号" }}
        <span v-if="selected?.scope === 'card'">
          · 个人笔记，仅限名片 {{ selected.card_code }}</span
        >
      </p>
      <NoteEditor
        :key="editorKey"
        :initial="draft"
        :busy="editTask.busy.value"
        @save="save"
        @dirty="dirty = true"
      />
    </div>
    <el-dialog
      v-model="uploading"
      title="批量上传 Markdown"
      width="1000px"
      :close-on-click-modal="false"
      ><KnowledgeUpload v-if="uploading" @saved="load()"
    /></el-dialog>
    <el-dialog
      :model-value="!!historyId"
      title="版本历史"
      width="760px"
      @update:model-value="
        (v) => {
          if (!v) historyId = '';
        }
      "
      ><HistoryPanel
        v-if="historyId"
        :key="historyId"
        :file-id="historyId"
        @restored="restored" /></el-dialog
    ><el-alert
      title="当前支持批量Markdown解析预览并逐篇存草稿、审核发布、撤回、历史和回滚；文件夹递归导入及评测运行尚未交付。"
      type="info"
      :closable="false"
    />
  </section>
</template>
