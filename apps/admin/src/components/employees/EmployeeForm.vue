<script setup lang="ts">
import { computed, reactive, useTemplateRef } from "vue";
import type { FormInstance, FormItemRule, FormRules } from "element-plus";
import type {
  Staff,
  EmployeeInput,
  EmployeeUpdate,
  CompanyOption,
} from "@/api/schema";
const props = defineProps<{
  initial: Staff | null;
  busy: boolean;
  companies: CompanyOption[];
  companiesState: "loading" | "ready" | "error";
  selfId?: number;
}>();
const emit = defineEmits<{
  create: [body: EmployeeInput];
  update: [body: EmployeeUpdate];
  reloadCompanies: [];
}>();
/** Edit keeps the exact server company_id; create starts at null = explicit primary default. */
const initialCompanyId =
  props.initial && props.initial.company_id && props.initial.company_id > 0
    ? props.initial.company_id
    : null;
const model = reactive({
  name: props.initial?.name ?? "",
  phone: props.initial?.phone ?? "",
  dept: props.initial?.dept ?? "",
  title: props.initial?.title ?? "",
  password: "",
  role: props.initial?.role ?? "employee",
  company_id: initialCompanyId,
});
const companiesReady = computed(() => props.companiesState === "ready");
/** Ensure the current assignment stays visible even if absent from the option list. */
const options = computed(() => {
  const list = props.companies.map((c) => ({
    id: c.id,
    label: c.is_primary ? `${c.name}（主公司）` : c.name,
  }));
  if (
    initialCompanyId &&
    props.initial &&
    !list.some((o) => o.id === initialCompanyId)
  )
    list.push({
      id: initialCompanyId,
      label: props.initial.company_name || `公司 #${initialCompanyId}`,
    });
  return list;
});
/** Admin accounts and the current operator must keep a phone (login identity). */
const phoneLocked = computed(
  () =>
    !!props.initial?.phone &&
    (props.initial.role === "admin" || props.initial.id === props.selfId),
);
const hasPhone = computed(() => model.phone.trim() !== "");
const passwordPattern = /^(?=.*[A-Za-z])(?=.*\d).{8,20}$/;
const phoneRule: FormItemRule = {
  validator: (_rule, value: string, callback) => {
    const v = value.trim();
    if (!v && (phoneLocked.value || model.role === "admin"))
      callback(new Error("管理员或当前账号不能清空手机号"));
    else if (v && !/^1[3-9]\d{9}$/.test(v))
      callback(new Error("请输入有效的11位手机号"));
    else callback();
  },
};
const passwordRule: FormItemRule = {
  validator: (_rule, value: string, callback) => {
    if (props.initial || !hasPhone.value) callback();
    else if (!value) callback(new Error("填写手机号时需设置初始密码"));
    else if (!passwordPattern.test(value))
      callback(new Error("请输入8–20位，至少含字母和数字（可含符号）"));
    else callback();
  },
};
const rules: FormRules = {
  name: [{ required: true, message: "请填写姓名" }],
  phone: [phoneRule],
  password: [passwordRule],
};
const form = useTemplateRef<FormInstance>("form");
async function save() {
  if (!companiesReady.value) return;
  if (!(await form.value?.validate().catch(() => false))) return;
  const phone = model.phone.trim();
  const base = {
    name: model.name.trim(),
    dept: model.dept,
    title: model.title,
  };
  if (props.initial) {
    const body: EmployeeUpdate = { ...base };
    if (phone !== (props.initial.phone ?? "")) body.phone = phone || null;
    // Only send company_id when the admin actually changed the assignment.
    if (model.company_id !== initialCompanyId)
      body.company_id = model.company_id;
    emit("update", body);
    return;
  }
  const company_id = model.company_id;
  // No phone → card profile only: omit phone/password, role must be employee.
  emit(
    "create",
    phone
      ? {
          ...base,
          company_id,
          phone,
          password: model.password,
          role: model.role,
          email: "",
          business_scope: "",
        }
      : {
          ...base,
          company_id,
          role: "employee",
          email: "",
          business_scope: "",
        },
  );
}
</script>
<template>
  <el-form
    ref="form"
    :model="model"
    :rules="rules"
    label-position="top"
    @submit.prevent="save"
    ><el-form-item label="姓名" prop="name"
      ><el-input
        v-model="model.name"
        aria-label="姓名"
        maxlength="80" /></el-form-item
    ><el-form-item label="任职公司"
      ><el-select
        v-model="model.company_id"
        aria-label="任职公司"
        :loading="companiesState === 'loading'"
        :disabled="!companiesReady"
        :placeholder="initial ? '请选择任职公司' : '默认：主公司'"
        :clearable="!initial"
        ><el-option
          v-for="o in options"
          :key="o.id"
          :label="o.label"
          :value="o.id" /></el-select
      ><el-alert
        v-if="companiesState === 'error'"
        type="warning"
        :closable="false"
        title="公司列表加载失败，暂不能保存，以免误改任职公司。"
        ><el-button link type="primary" @click="emit('reloadCompanies')"
          >重试加载</el-button
        ></el-alert
      ><span v-else-if="companiesState === 'loading'" class="muted"
        >正在加载公司列表…</span
      ><span v-else class="muted">{{
        initial
          ? "保持不变则不修改任职公司；产品目录仅在主公司名片展示。"
          : "留空即主公司；产品目录仅在主公司名片展示。"
      }}</span></el-form-item
    ><el-form-item label="手机号（选填）" prop="phone"
      ><el-input
        v-model="model.phone"
        aria-label="手机号（选填）"
        maxlength="11"
        inputmode="tel"
        :clearable="!phoneLocked"
      /><span class="muted">{{
        initial
          ? initial.login_enabled
            ? "清空手机号将关闭登录并撤销会话。"
            : "补填手机号不会自动开通登录，需再通过“设置登录密码”开通。"
          : "不填手机号则创建名片档案，不开通登录。"
      }}</span></el-form-item
    ><el-form-item label="部门"
      ><el-input
        v-model="model.dept"
        aria-label="部门"
        maxlength="120" /></el-form-item
    ><el-form-item label="职务"
      ><el-input
        v-model="model.title"
        aria-label="职务"
        maxlength="120" /></el-form-item
    ><template v-if="!initial && hasPhone"
      ><el-form-item label="角色"
        ><el-select v-model="model.role" aria-label="角色"
          ><el-option label="员工" value="employee" /><el-option
            label="管理员"
            value="admin" /></el-select></el-form-item
      ><el-form-item label="初始密码" prop="password"
        ><el-input
          v-model="model.password"
          aria-label="初始密码"
          type="password"
          show-password
          autocomplete="new-password"
          maxlength="20"
        /><span class="muted"
          >首次登录需修改密码。请通过安全渠道交付口令。</span
        ></el-form-item
      ></template
    ><el-button
      type="primary"
      native-type="submit"
      :loading="busy"
      :disabled="!companiesReady"
      >{{ !initial && !hasPhone ? "保存名片档案" : "保存员工" }}</el-button
    ></el-form
  >
</template>
