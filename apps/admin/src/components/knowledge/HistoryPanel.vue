<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api } from "@/api/adapters";
import type { Revision } from "@/api/schema";
import { useTask, confirmAction } from "@/composables/useTask";
import LoadState from "@/components/LoadState.vue";
const props = defineProps<{ fileId: string }>();
const emit = defineEmits<{ restored: [] }>();
const rows = ref<Revision[]>([]);
const { busy, error, run } = useTask();
async function load() {
  await run(async () => {
    rows.value = await api.history(props.fileId);
  });
}
async function rollback(row: Revision) {
  if (
    !(await confirmAction(
      `回滚到版本 ${row.revision}？会恢复该版本正文及公开/批准状态，请确认资料仍可公开。`,
    ))
  )
    return;
  await run(async () => {
    await api.rollback(props.fileId, row.revision);
    emit("restored");
  });
}
onMounted(load);
</script>
<template>
  <LoadState :busy="busy" :error="error" @retry="load" /><el-table
    :data="rows"
    empty-text="暂无历史版本"
    ><el-table-column prop="revision" label="版本" /><el-table-column
      prop="title"
      label="标题"
    /><el-table-column label="操作" width="120"
      ><template #default="{ row }"
        ><el-button link type="warning" :disabled="busy" @click="rollback(row)"
          >回滚此版本</el-button
        ></template
      ></el-table-column
    ></el-table
  >
</template>
