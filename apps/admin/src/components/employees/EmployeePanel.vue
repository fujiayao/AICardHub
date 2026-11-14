<script setup lang="ts">
import { shallowRef, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { api } from "@/api/adapters";
import type { Staff, EmployeeInput, EmployeeUpdate } from "@/api/schema";
import { useAuthStore } from "@/store/modules/auth";
import { usePage } from "@/composables/usePage";
import { useTask, confirmAction } from "@/composables/useTask";
import LoadState from "@/components/LoadState.vue";
import EmployeeTable from "./EmployeeTable.vue";
import EmployeeForm from "./EmployeeForm.vue";
import EmployeeActions from "./EmployeeActions.vue";
import CardEditor from "./CardEditor.vue";
const auth = useAuthStore(),
  q = shallowRef(""),
  search = shallowRef("");
const { data, page, busy, error, load } = usePage((p) =>
  api.employees({ page: p, page_size: 20, q: search.value }),
);
const mutate = useTask();
const open = shallowRef(false),
  selected = shallowRef<Staff | null>(null),
  action = shallowRef<"reset" | "transfer" | null>(null),
  card = shallowRef<Staff | null>(null);
function edit(staff?: Staff) {
  selected.value = staff ?? null;
  open.value = true;
}
async function find() {
  search.value = q.value.trim();
  await load(1);
}
async function save(body: EmployeeInput | EmployeeUpdate) {
  await mutate.run(async () => {
    if (selected.value) await api.updateEmployee(selected.value.id, body);
    else if ("password" in body) await api.createEmployee(body);
    else throw new Error("初始密码缺失");
    open.value = false;
    ElMessage.success("员工已保存");
    await load();
  });
}
async function disable(staff: Staff) {
  if (staff.id === auth.session?.staff.id) return;
  if (
    !(await confirmAction(
      `停用 ${staff.name}？个人名片将不再公开，仍保留公司联络信息。离职请先确认转交。`,
    ))
  )
    return;
  await mutate.run(async () => {
    await api.disableEmployee(staff.id);
    ElMessage.success("员工已停用");
    await load();
  });
}
function start(mode: "reset" | "transfer", staff: Staff) {
  selected.value = staff;
  action.value = mode;
}
async function done() {
  action.value = null;
  await load();
}
onMounted(() => load());
</script>
<template>
  <section class="page">
    <div>
      <h1>员工与名片</h1>
      <p class="muted">
        创建员工后自动开通名片与助手。不能停用或转交当前管理员身份。
      </p>
    </div>
    <div class="panel">
      <form class="toolbar" @submit.prevent="find">
        <el-input
          v-model="q"
          placeholder="搜索姓名或手机号"
          clearable
          aria-label="搜索员工"
        /><el-button native-type="submit" :loading="busy">搜索</el-button
        ><el-button type="primary" @click="edit()">新增员工</el-button
        ><el-button :loading="busy" @click="load()">刷新</el-button>
      </form>
      <LoadState
        :busy="busy"
        :error="error || mutate.error.value"
        @retry="load()"
      /><EmployeeTable
        :rows="data.items"
        :self-id="auth.session?.staff.id"
        :busy="busy || mutate.busy.value"
        @edit="edit"
        @disable="disable"
        @reset="start('reset', $event)"
        @transfer="start('transfer', $event)"
        @card="card = $event"
      /><el-pagination
        v-model:current-page="page"
        :total="data.total"
        :page-size="20"
        layout="prev,pager,next,total"
        @current-change="load"
      />
    </div>
    <el-dialog
      v-model="open"
      :title="selected ? '编辑员工' : '新增员工'"
      width="600px"
      :close-on-click-modal="false"
      ><EmployeeForm
        v-if="open"
        :initial="selected"
        :busy="mutate.busy.value"
        @save="save" /></el-dialog
    ><el-dialog
      :model-value="!!action"
      :title="action === 'reset' ? '重置密码' : '离职转交'"
      width="540px"
      :close-on-click-modal="false"
      @update:model-value="
        (v) => {
          if (!v) action = null;
        }
      "
      ><EmployeeActions
        v-if="action && selected"
        :key="`${selected.id}-${action}`"
        :staff="selected"
        :mode="action"
        :self-id="auth.session?.staff.id"
        @done="done" /></el-dialog
    ><el-drawer
      :model-value="!!card"
      title="代改名片与 AI 助手"
      size="min(760px,100vw)"
      :close-on-click-modal="false"
      @update:model-value="
        (v) => {
          if (!v) card = null;
        }
      "
      ><CardEditor v-if="card?.card_code" :code="card.card_code" /></el-drawer
    ><el-alert
      title="Excel 批量导入、独立启用接口不在本地冻结契约内，当前仅交付新增、修改、停用、重置、转交及代改。"
      type="info"
      :closable="false"
    />
  </section>
</template>
