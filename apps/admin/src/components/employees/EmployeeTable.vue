<script setup lang="ts">
import { PureTable } from "@pureadmin/table";
import { maskPhone, staffEnabled, loginEnabled } from "@/api/adapters";
import type { Staff } from "@/api/schema";
defineProps<{ rows: Staff[]; selfId?: number; busy: boolean }>();
defineEmits<{
  edit: [staff: Staff];
  disable: [staff: Staff];
  reset: [staff: Staff];
  transfer: [staff: Staff];
  card: [staff: Staff];
}>();
const noPhoneReason = "未提供手机号，无法设置登录密码；请先编辑补填手机号";
const columns = [
  { label: "姓名", prop: "name", minWidth: 100 },
  { label: "类型", slot: "kind", width: 100 },
  { label: "任职公司", slot: "company", minWidth: 140 },
  { label: "手机", slot: "phone", minWidth: 120 },
  { label: "登录状态", slot: "login", width: 110 },
  { label: "部门", prop: "dept" },
  { label: "职务", prop: "title" },
  { label: "状态", slot: "status", width: 80 },
  { label: "角色", slot: "role", width: 80 },
  { label: "操作", slot: "actions", minWidth: 380 },
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
    <template #kind="{ row }">{{
      loginEnabled(row) ? "员工账号" : "名片档案"
    }}</template>
    <template #company="{ row }">{{ row.company_name || "—" }}</template>
    <template #phone="{ row }"
      ><span :class="{ muted: !row.phone }">{{
        maskPhone(row.phone)
      }}</span></template
    >
    <template #login="{ row }"
      ><el-tag :type="loginEnabled(row) ? 'success' : 'info'">{{
        loginEnabled(row) ? "已开通登录" : "未开通登录"
      }}</el-tag></template
    >
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
      ><el-tooltip v-if="!row.phone" :content="noPhoneReason" placement="top"
        ><span
          ><el-button
            link
            type="primary"
            disabled
            :aria-label="`设置登录密码：${noPhoneReason}`"
            >设置登录密码</el-button
          ></span
        ></el-tooltip
      ><el-button
        v-else
        link
        type="primary"
        :disabled="busy"
        @click="$emit('reset', row)"
        >{{ loginEnabled(row) ? "重置密码" : "设置登录密码" }}</el-button
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
