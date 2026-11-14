<script setup lang="ts">
import { onMounted, shallowRef } from "vue";
import { ElMessage } from "element-plus";
import { api } from "@/api/adapters";
import type { Issue, IssueStatus } from "@/api/schema";
import { usePage } from "@/composables/usePage";
import { useTask, confirmAction } from "@/composables/useTask";
import LoadState from "@/components/LoadState.vue";
const status = shallowRef("");
const { data, page, busy, error, load } = usePage((p) =>
  api.issues({ page: p, page_size: 20, status: status.value }),
);
const action = useTask();
async function update(row: Issue, next: IssueStatus) {
  if (
    !(await confirmAction(
      `将此问题标记为“${next === "resolved" ? "已处理" : "忽略"}”？此操作不会自动发布知识。`,
    ))
  )
    return;
  await action.run(async () => {
    await api.issue(row.id, next);
    await load();
    ElMessage.success("问题状态已更新");
  });
}
onMounted(() => load());
</script>
<template>
  <section class="page">
    <div>
      <h1>问题池</h1>
      <p class="muted">
        处理员工提交的问题。需要补充公开知识时，请在知识库单独审核发布。
      </p>
    </div>
    <div class="panel">
      <div class="toolbar">
        <el-select
          v-model="status"
          placeholder="全部状态"
          clearable
          style="width: 180px"
          @change="load(1)"
          ><el-option label="待处理" value="open" /><el-option
            label="已处理"
            value="resolved" /><el-option
            label="已忽略"
            value="ignored" /></el-select
        ><el-button :loading="busy" @click="load()">刷新</el-button>
      </div>
      <LoadState
        :busy="busy"
        :error="error || action.error.value"
        @retry="load()"
      /><el-table :data="data.items" empty-text="没有符合条件的问题"
        ><el-table-column
          prop="question"
          label="问题内容"
          min-width="300"
        /><el-table-column prop="status" label="状态" /><el-table-column
          prop="created_at"
          label="提交时间"
          min-width="180"
        /><el-table-column label="操作" min-width="180"
          ><template #default="{ row }"
            ><el-button
              link
              type="primary"
              :disabled="row.status === 'resolved' || action.busy.value"
              @click="update(row, 'resolved')"
              >标记已处理</el-button
            ><el-button
              link
              :disabled="row.status === 'ignored' || action.busy.value"
              @click="update(row, 'ignored')"
              >忽略</el-button
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
  </section>
</template>
