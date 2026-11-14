<script setup lang="ts">
import { shallowRef, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { api } from "@/api/adapters";
import type {
  Staff,
  EmployeeInput,
  EmployeeUpdate,
  CompanyOption,
} from "@/api/schema";
import { useAuthStore } from "@/store/modules/auth";
import { usePage } from "@/composables/usePage";
import { useTask, confirmAction } from "@/composables/useTask";
import LoadState from "@/components/LoadState.vue";
import EmployeeTable from "./EmployeeTable.vue";
import EmployeeForm from "./EmployeeForm.vue";
import EmployeeActions from "./EmployeeActions.vue";
import EmployeeImport from "./EmployeeImport.vue";
import CardEditor from "./CardEditor.vue";
import PageHeader from "@/components/shared/PageHeader.vue";
const auth = useAuthStore(),
  q = shallowRef(""),
  search = shallowRef("");
const { data, page, busy, error, load } = usePage((p) =>
  api.employees({ page: p, page_size: 20, q: search.value }),
);
const mutate = useTask();
const importing = shallowRef(false);
const companies = shallowRef<CompanyOption[]>([]),
  companyError = shallowRef(""),
  companiesState = shallowRef<"loading" | "ready" | "error">("loading");
const open = shallowRef(false),
  selected = shallowRef<Staff | null>(null),
  action = shallowRef<"reset" | "transfer" | null>(null),
  card = shallowRef<Staff | null>(null);
async function loadCompanies() {
  companiesState.value = "loading";
  try {
    companies.value = await api.companies();
    companyError.value = "";
    companiesState.value = "ready";
  } catch (e) {
    companyError.value = e instanceof Error ? e.message : "公司列表加载失败";
    companiesState.value = "error";
  }
}
function edit(staff?: Staff) {
  selected.value = staff ?? null;
  open.value = true;
}
async function find() {
  search.value = q.value.trim();
  await load(1);
}
async function persist(task: () => Promise<unknown>) {
  await mutate.run(async () => {
    await task();
    open.value = false;
    ElMessage.success("员工已保存");
    await load();
  });
}
const create = (body: EmployeeInput) => persist(() => api.createEmployee(body));
const update = (body: EmployeeUpdate) => {
  const target = selected.value;
  return target
    ? persist(() => api.updateEmployee(target.id, body))
    : undefined;
};
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
onMounted(() => {
  void load();
  void loadCompanies();
});
</script>
<template>
  <section class="page">
    <PageHeader
      title="员工与名片"
      desc="创建员工后自动开通名片与助手；不填手机号即为名片档案，不开通登录。不能停用或转交当前管理员身份。"
    >
      <el-button type="primary" @click="edit()">新增员工 / 名片档案</el-button
      ><el-button @click="importing = true">Excel 导入</el-button>
    </PageHeader>
    <div class="panel">
      <el-alert
        v-if="companyError"
        type="warning"
        :closable="false"
        :title="`公司列表加载失败：${companyError}（恢复前不能新增或编辑员工）`"
        ><el-button link type="primary" @click="loadCompanies"
          >重试</el-button
        ></el-alert
      >
      <form class="toolbar" @submit.prevent="find">
        <el-input
          v-model="q"
          placeholder="搜索姓名或手机号"
          clearable
          aria-label="搜索员工"
        /><el-button native-type="submit" :loading="busy">搜索</el-button
        ><el-button :loading="busy" @click="load()">刷新</el-button>
      </form>
      <LoadState
        :busy="busy"
        :error="error || mutate.error.value"
        @retry="load()"
      />
      <div class="table-wrap">
        <EmployeeTable
          :rows="data.items"
          :self-id="auth.session?.staff.id"
          :busy="busy || mutate.busy.value"
          @edit="edit"
          @disable="disable"
          @reset="start('reset', $event)"
          @transfer="start('transfer', $event)"
          @card="card = $event"
        />
      </div>
      <el-pagination
        v-model:current-page="page"
        :total="data.total"
        :page-size="20"
        layout="prev,pager,next,total"
        @current-change="load"
      />
    </div>
    <el-dialog
      v-model="importing"
      title="Excel 导入员工"
      width="min(900px, 100vw)"
      :close-on-click-modal="false"
      ><EmployeeImport v-if="importing" @imported="load()"
    /></el-dialog>
    <el-dialog
      v-model="open"
      :title="selected ? '编辑员工' : '新增员工 / 名片档案'"
      width="min(560px, 100vw)"
      :close-on-click-modal="false"
      ><EmployeeForm
        v-if="open"
        :initial="selected"
        :busy="mutate.busy.value"
        :companies="companies"
        :companies-state="companiesState"
        :self-id="auth.session?.staff.id"
        @reload-companies="loadCompanies"
        @create="create"
        @update="update" /></el-dialog
    ><el-dialog
      :model-value="!!action"
      :title="
        action === 'transfer'
          ? '离职转交'
          : selected?.login_enabled
            ? '重置密码'
            : '设置登录密码'
      "
      width="min(560px, 100vw)"
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
      title="Excel 导入会逐行创建并显示结果。物理 NFC 管理暂缓；独立启用操作仍未交付。"
      type="info"
      :closable="false"
    />
  </section>
</template>
