<script setup lang="ts">
import { reactive, useTemplateRef } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import type { CampaignInput, CampaignStatus } from "@/api/schema";
import {
  campaignStatuses,
  statusLabels,
  toCampaignInput,
} from "./campaignMeta";

const props = defineProps<{
  initial: CampaignInput;
  busy: boolean;
  /** Status persisted on the server; ended campaigns cannot be reactivated. */
  savedStatus: CampaignStatus | null;
}>();
const emit = defineEmits<{ save: [value: CampaignInput]; cancel: [] }>();

const MAX_GUIDES = 6;
function toDate(value: string): Date | null {
  if (!value) return null;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}
const init = toCampaignInput(props.initial);
const model = reactive({
  name: init.name,
  status: init.status ?? "draft",
  start: toDate(init.start_at),
  end: toDate(init.end_at),
  booth: init.booth ?? "",
  location: init.location ?? "",
  opening_override: init.opening_override ?? "",
  guides: [...(init.guide_override ?? [])],
});
const locked = props.savedStatus === "ended";
const statusOptions = campaignStatuses.map((value) => ({
  value,
  label: statusLabels[value],
}));
const form = useTemplateRef<FormInstance>("form");
type Cb = (e?: Error) => void;
const rules: FormRules = {
  name: [
    { required: true, whitespace: true, message: "请输入活动名称" },
    { max: 120, message: "活动名称最多 120 字" },
  ],
  status: [{ required: true, message: "请选择状态" }],
  start: [{ required: true, message: "请选择开始时间" }],
  end: [
    { required: true, message: "请选择结束时间" },
    {
      validator: (_r: unknown, v: Date | null, cb: Cb) =>
        cb(
          v && model.start && v.getTime() <= model.start.getTime()
            ? new Error("结束时间必须晚于开始时间")
            : undefined,
        ),
    },
  ],
  booth: [{ max: 80, message: "展位最多 80 字" }],
  location: [{ max: 255, message: "地点最多 255 字" }],
  opening_override: [{ max: 2000, message: "开场白最多 2000 字" }],
  guides: [
    {
      validator: (_r: unknown, v: string[], cb: Cb) => {
        const items = v.map((s) => s.trim()).filter(Boolean);
        if (v.some((s) => !s.trim()))
          return cb(new Error("引导问题不能为空，请填写或删除空行"));
        if (items.length > MAX_GUIDES)
          return cb(new Error("最多 6 条引导问题"));
        if (items.some((s) => s.length > 255))
          return cb(new Error("每条引导问题最多 255 字"));
        cb();
      },
    },
  ],
};
function addGuide() {
  if (model.guides.length < MAX_GUIDES) model.guides.push("");
}
function removeGuide(index: number) {
  model.guides.splice(index, 1);
}
async function save() {
  if (!(await form.value?.validate().catch(() => false))) return;
  if (!model.start || !model.end) return;
  emit("save", {
    name: model.name.trim(),
    status: locked ? "ended" : model.status,
    // toISOString() always serializes as UTC with a "Z" suffix.
    start_at: model.start.toISOString(),
    end_at: model.end.toISOString(),
    booth: model.booth.trim(),
    location: model.location.trim(),
    opening_override: model.opening_override.trim(),
    guide_override: model.guides.map((s) => s.trim()).filter(Boolean),
  });
}
</script>
<template>
  <el-form
    ref="form"
    :model="model"
    :rules="rules"
    label-position="top"
    aria-label="活动表单"
    @submit.prevent="save"
  >
    <el-form-item label="活动名称" prop="name">
      <el-input v-model="model.name" maxlength="120" show-word-limit />
    </el-form-item>
    <el-form-item label="状态" prop="status">
      <el-radio-group
        v-model="model.status"
        :disabled="locked"
        aria-label="活动状态"
      >
        <el-radio-button
          v-for="opt in statusOptions"
          :key="opt.value"
          :value="opt.value"
          :disabled="locked && opt.value !== 'ended'"
          >{{ opt.label }}</el-radio-button
        >
      </el-radio-group>
      <p v-if="locked" class="hint">
        已结束的活动不可重新启用，以保留历史归因。
      </p>
      <p v-else class="hint">已启用且处于有效期内的活动才会对访客生效。</p>
    </el-form-item>
    <div class="time-grid">
      <el-form-item label="开始时间" prop="start">
        <el-date-picker
          v-model="model.start"
          type="datetime"
          placeholder="选择开始时间"
          aria-label="开始时间"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item label="结束时间" prop="end">
        <el-date-picker
          v-model="model.end"
          type="datetime"
          placeholder="选择结束时间"
          aria-label="结束时间"
          style="width: 100%"
        />
      </el-form-item>
    </div>
    <div class="time-grid">
      <el-form-item label="展位" prop="booth">
        <el-input
          v-model="model.booth"
          maxlength="80"
          placeholder="如 A1-203"
        />
      </el-form-item>
      <el-form-item label="地点" prop="location">
        <el-input v-model="model.location" maxlength="255" />
      </el-form-item>
    </div>
    <el-form-item
      label="活动开场白（可选，覆盖模板开场白）"
      prop="opening_override"
    >
      <el-input
        v-model="model.opening_override"
        type="textarea"
        :rows="3"
        maxlength="2000"
        show-word-limit
      />
    </el-form-item>
    <el-form-item
      :label="`活动引导问题（可选，最多 ${MAX_GUIDES} 条）`"
      prop="guides"
    >
      <div class="guides">
        <div v-for="(_, i) in model.guides" :key="i" class="guide-row">
          <el-input
            v-model="model.guides[i]"
            maxlength="255"
            :aria-label="`引导问题 ${i + 1}`"
            :placeholder="`引导问题 ${i + 1}`"
          />
          <el-button
            link
            type="danger"
            :aria-label="`删除引导问题 ${i + 1}`"
            @click="removeGuide(i)"
            >删除</el-button
          >
        </div>
        <el-button
          :disabled="model.guides.length >= MAX_GUIDES"
          @click="addGuide"
          >添加引导问题</el-button
        >
      </div>
    </el-form-item>
    <div class="actions">
      <el-button :disabled="busy" @click="emit('cancel')">取消</el-button>
      <el-button native-type="submit" type="primary" :loading="busy"
        >保存活动</el-button
      >
    </div>
  </el-form>
</template>
<style scoped>
.time-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0 var(--ac-space-4);
}
.hint {
  margin: var(--ac-space-1) 0 0;
  font-size: 12px;
  color: var(--ac-text-subtle);
  width: 100%;
}
.guides {
  display: flex;
  flex-direction: column;
  gap: var(--ac-space-2);
  width: 100%;
}
.guide-row {
  display: flex;
  gap: var(--ac-space-2);
  align-items: center;
}
.actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--ac-space-2);
}
</style>
