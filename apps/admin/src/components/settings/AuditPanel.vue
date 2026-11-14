<script setup lang="ts">
import { onMounted } from "vue";
import { api } from "@/api/adapters";
import { usePage } from "@/composables/usePage";
import LoadState from "@/components/LoadState.vue";
const { data, page, busy, error, load } = usePage((p) =>
  api.audits({ page: p, page_size: 20 }),
);
onMounted(() => load());
</script>
<template>
  <section class="panel">
    <div class="toolbar">
      <h2>操作审计</h2>
      <el-button :loading="busy" @click="load()">刷新</el-button>
    </div>
    <LoadState :busy="busy" :error="error" @retry="load()" /><el-table
      :data="data.items"
      empty-text="暂无审计记录"
      ><el-table-column prop="action" label="操作" /><el-table-column
        prop="operator_id"
        label="操作者" /><el-table-column
        prop="target"
        label="目标" /><el-table-column
        prop="created_at"
        label="时间"
        min-width="180" /></el-table
    ><el-pagination
      v-model:current-page="page"
      :total="data.total"
      :page-size="20"
      layout="prev,pager,next,total"
      @current-change="load"
    />
    <p class="muted">仅显示操作元数据，不展示可能含敏感信息的原始审计载荷。</p>
  </section>
</template>
