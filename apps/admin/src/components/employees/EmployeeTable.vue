<script setup lang="ts">
import { PureTable } from "@pureadmin/table";
import { maskPhone, staffEnabled } from "@/api/adapters";
import type { Staff } from "@/api/schema";
defineProps<{ rows: Staff[]; selfId?: number; busy: boolean }>();
defineEmits<{
  edit: [staff: Staff];
  disable: [staff: Staff];
  reset: [staff: Staff];
  transfer: [staff: Staff];
  card: [staff: Staff];
}>();
const columns = [
  { label: "姓名", prop: "name", minWidth: 100 },
  { label: "手机", slot: "phone", minWidth: 130 },
  { label: "部门", prop: "dept" },
  { label: "职务", prop: "title" },
  { label: "状态", slot: "status", width: 90 },
  { label: "角色", slot: "role", width: 100 },
  { label: "操作", slot: "actions", minWidth: 360 },
];
</script>
<template>
  <PureTable
    :data="rows"
    :columns="columns"
    row-key="id"
    border
    :loading="busy"
    empty-text="暂无员工，请新增或调整搜索条件"
  >
    <template #phone="{ row }">{{ maskPhone(row.phone) }}</template>
    <template #status="{ row }"
      ><el-tag :type="staffEnabled(row) ? 'success' : 'info'">{{
        staffEnabled(row) ? "启用" : "停用"
      }}</el-tag></template
    >
    <template #role="{ row }">{{
      row.role === "admin" ? "管理员" : "员工"
    }}</template>
    <template #actions="{ row }"
      ><el-button
        link
        type="primary"
        :disabled="busy"
        @click="$emit('edit', row)"
        >编辑</el-button
      ><el-button
        link
        type="primary"
        :disabled="!row.card_code || busy"
        @click="$emit('card', row)"
        >名片 / 助手</el-button
      ><el-button
        link
        type="primary"
        :disabled="busy"
        @click="$emit('reset', row)"
        >重置密码</el-button
      ><el-button
        link
        type="warning"
        :disabled="row.id === selfId || !staffEnabled(row) || busy"
        @click="$emit('transfer', row)"
        >转交</el-button
      ><el-button
        link
        type="danger"
        :disabled="row.id === selfId || !staffEnabled(row) || busy"
        @click="$emit('disable', row)"
        >停用</el-button
      ></template
    >
  </PureTable>
</template>
