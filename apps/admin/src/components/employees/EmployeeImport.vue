<script setup lang="ts">
import { ref, shallowRef } from "vue";
import { ElMessage, type UploadFile } from "element-plus";
import { api, maskPhone } from "@/api/adapters";
import type { EmployeeImportResult } from "@/api/schema";
import { useTask, confirmAction } from "@/composables/useTask";
import LoadState from "@/components/LoadState.vue";
const emit = defineEmits<{ imported: [] }>();
const file = shallowRef<File>(),
  result = ref<EmployeeImportResult>();
const { busy, error, run } = useTask();
function select(upload: UploadFile) {
  const selected = upload.raw;
  if (!selected) return;
  if (
    !selected.name.toLowerCase().endsWith(".xlsx") ||
    selected.size > 20 * 1024 * 1024
  ) {
    ElMessage.warning("请选择20MB以内的.xlsx文件");
    file.value = undefined;
    return;
  }
  file.value = selected;
  result.value = undefined;
}
async function submit() {
  if (!file.value) return;
  if (
    !(await confirmAction(
      "确认按行创建员工？成功行将立即开通名片和助手；失败行不创建，不能自动撤销整批。",
    ))
  )
    return;
  await run(async () => {
    if (!file.value) return;
    result.value = await api.importEmployees(file.value);
    file.value = undefined;
    emit("imported");
  });
}
</script>
<template>
  <section>
    <el-alert
      title="仅导入本组织获授权员工资料。导入会立即创建成功行，首次登录强制改密；部分失败时只修正失败行，勿重传成功行。"
      type="warning"
      :closable="false"
    />
    <p>
      Excel 第一行表头必须包含
      <code>姓名</code>、<code>手机号</code>、<code>初始密码</code>；可选
      <code>部门</code
      >、<code>职位</code>、<code>邮箱</code>、<code>负责业务</code>、<code>角色</code>。角色用
      employee/admin，默认 employee。
    </p>
    <p class="muted">
      也支持英文表头 name / phone / password / dept / title / email /
      business_scope /
      role。最多500行、20MB、仅第一个工作表；手机号用文本，禁止公式单元格；初始密码使用8–20位且至少含字母和数字（可含符号）。
    </p>
    <el-upload
      :auto-upload="false"
      :show-file-list="false"
      accept=".xlsx"
      :disabled="busy"
      :on-change="select"
      ><el-button>选择员工 Excel</el-button></el-upload
    >
    <p class="muted">{{ file?.name ?? "尚未选择文件" }}</p>
    <el-button
      type="primary"
      :disabled="!file || busy"
      :loading="busy"
      @click="submit"
      >确认导入员工</el-button
    ><LoadState :busy="busy" :error="error" @retry="submit" /><template
      v-if="result"
      ><p>
        成功 {{ result.items.filter((item) => item.ok).length }} 行；失败
        {{ result.items.filter((item) => !item.ok).length }} 行。
      </p>
      <el-table :data="result.items" empty-text="文件没有可导入的数据行"
        ><el-table-column
          prop="row"
          label="Excel行号"
          width="100"
        /><el-table-column label="结果" width="90"
          ><template #default="{ row }"
            ><el-tag :type="row.ok ? 'success' : 'danger'">{{
              row.ok ? "已创建" : "失败"
            }}</el-tag></template
          ></el-table-column
        ><el-table-column
          prop="message"
          label="说明"
          min-width="180"
        /><el-table-column label="员工" min-width="140"
          ><template #default="{ row }">{{
            row.employee?.name ?? "—"
          }}</template></el-table-column
        ><el-table-column label="手机号" min-width="130"
          ><template #default="{ row }">{{
            row.employee ? maskPhone(row.employee.phone) : "—"
          }}</template></el-table-column
        ><el-table-column label="名片编号" min-width="130"
          ><template #default="{ row }">{{
            row.employee?.card_code ?? "—"
          }}</template></el-table-column
        ></el-table
      ></template
    >
  </section>
</template>
