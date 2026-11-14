<script setup lang="ts">
import { onMounted, shallowRef } from "vue";
import { api, maskPhone } from "@/api/adapters";
import { usePage } from "@/composables/usePage";
import LoadState from "@/components/LoadState.vue";
const status = shallowRef("");
const statusText: Record<string, string> = {
  new: "新线索",
  contacted: "已联系",
  converted: "已转化",
  invalid: "无效",
};
const statusType: Record<string, "primary" | "success" | "info" | "warning"> = {
  new: "warning",
  contacted: "primary",
  converted: "success",
  invalid: "info",
};
const { data, page, busy, error, load } = usePage((p) =>
  api.leads({ page: p, page_size: 20, status: status.value }),
);
function filter() {
  page.value = 1;
  void load(1);
}
const time = (v: string) =>
  new Date(v).toLocaleString("zh-CN", { hour12: false });
onMounted(() => load());
</script>
<template>
  <section class="panel" aria-labelledby="leads-title">
    <div class="panel-head">
      <h2 id="leads-title">全部线索</h2>
      <div class="actions">
        <el-select
          v-model="status"
          aria-label="按状态筛选线索"
          class="status-select"
          @change="filter"
        >
          <el-option label="全部状态" value="" />
          <el-option
            v-for="(label, key) in statusText"
            :key="key"
            :label="label"
            :value="key"
          />
        </el-select>
        <el-button :loading="busy" @click="load()">刷新</el-button>
      </div>
    </div>
    <LoadState :busy="busy" :error="error" @retry="load()" />
    <div v-if="!error" class="table-wrap">
      <el-table :data="data.items" empty-text="尚无线索">
        <el-table-column prop="name" label="姓名" min-width="100" />
        <el-table-column label="电话" min-width="130"
          ><template #default="{ row }">{{
            maskPhone(row.phone)
          }}</template></el-table-column
        >
        <el-table-column prop="company_name" label="公司" min-width="140" />
        <el-table-column
          prop="need"
          label="需求"
          min-width="200"
          show-overflow-tooltip
        />
        <el-table-column label="状态" min-width="90"
          ><template #default="{ row }"
            ><el-tag :type="statusType[row.status]" size="small">{{
              statusText[row.status] ?? row.status
            }}</el-tag></template
          ></el-table-column
        >
        <el-table-column label="创建时间" min-width="170"
          ><template #default="{ row }">{{
            time(row.created_at)
          }}</template></el-table-column
        >
      </el-table>
    </div>
    <el-pagination
      v-model:current-page="page"
      :total="data.total"
      :page-size="20"
      layout="prev,pager,next,total"
      @current-change="load"
    />
  </section>
</template>
<style scoped>
.actions {
  display: flex;
  gap: var(--ac-space-2);
  flex-wrap: wrap;
}
.status-select {
  width: 140px;
}
</style>
