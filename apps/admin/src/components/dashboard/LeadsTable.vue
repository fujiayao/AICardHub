<script setup lang="ts">
import { onMounted } from "vue";
import { api, maskPhone } from "@/api/adapters";
import { usePage } from "@/composables/usePage";
import LoadState from "@/components/LoadState.vue";
const { data, page, busy, error, load } = usePage((p) =>
  api.leads({ page: p, page_size: 20 }),
);
onMounted(() => load());
</script>
<template>
  <section class="panel">
    <div class="toolbar">
      <h2>全局线索</h2>
      <el-button :loading="busy" @click="load()">刷新</el-button>
    </div>
    <LoadState :busy="busy" :error="error" @retry="load()" /><el-table
      v-if="!error"
      :data="data.items"
      empty-text="尚无线索"
      ><el-table-column prop="name" label="姓名" /><el-table-column label="电话"
        ><template #default="{ row }">{{
          maskPhone(row.phone)
        }}</template></el-table-column
      ><el-table-column prop="company_name" label="公司" /><el-table-column
        prop="need"
        label="需求"
        show-overflow-tooltip /><el-table-column
        prop="status"
        label="状态" /><el-table-column
        prop="created_at"
        label="创建时间"
        min-width="180" /></el-table
    ><el-pagination
      v-model:current-page="page"
      :total="data.total"
      :page-size="20"
      layout="prev,pager,next,total"
      @current-change="load"
    />
  </section>
</template>
