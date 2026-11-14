<script setup lang="ts">
import type { Campaign } from "@/api/schema";
import { formatTime, statusLabels, statusTagType } from "./campaignMeta";

defineProps<{ rows: Campaign[]; busy: boolean }>();
defineEmits<{
  view: [row: Campaign];
  edit: [row: Campaign];
  remove: [row: Campaign];
  report: [row: Campaign];
}>();
const labelOf = (row: Campaign) => statusLabels[row.status];
const tagOf = (row: Campaign) => statusTagType[row.status];
</script>
<template>
  <div class="table-wrap" role="region" aria-label="活动列表" tabindex="0">
    <el-table :data="rows" empty-text="暂无活动" row-key="id">
      <el-table-column prop="name" label="活动名称" min-width="180" show-overflow-tooltip />
      <el-table-column label="状态" width="190">
        <template #default="{ row }">
          <div class="tags">
            <el-tag :type="tagOf(row)">{{ labelOf(row) }}</el-tag>
            <el-tag v-if="row.is_live" type="success" effect="dark">当前生效</el-tag>
            <el-tag v-else type="info" effect="plain">未在有效期</el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="活动时间" min-width="210">
        <template #default="{ row }">
          <div class="time">
            <span>{{ formatTime(row.start_at) }}</span>
            <span class="muted">至 {{ formatTime(row.end_at) }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="展位 / 地点" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">
          {{ [row.booth, row.location].filter(Boolean).join(" · ") || "—" }}
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="250" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :aria-label="`查看活动 ${row.name}`" @click="$emit('view', row)"
            >查看</el-button
          >
          <el-button link type="primary" :disabled="busy" :aria-label="`编辑活动 ${row.name}`" @click="$emit('edit', row)"
            >编辑</el-button
          >
          <el-button link type="primary" :aria-label="`查看活动 ${row.name} 的报表`" @click="$emit('report', row)"
            >查看报表</el-button
          >
          <el-button
            link
            type="danger"
            :disabled="busy || row.status !== 'draft'"
            :title="row.status !== 'draft' ? '仅未被使用的草稿活动可删除' : undefined"
            :aria-label="`删除活动 ${row.name}`"
            @click="$emit('remove', row)"
            >删除</el-button
          >
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
<style scoped>
.table-wrap {
  overflow-x: auto;
  max-width: 100%;
}
.table-wrap:focus-visible {
  outline: 2px solid var(--ac-focus);
  outline-offset: 2px;
}
.tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--ac-space-1);
}
.time {
  display: flex;
  flex-direction: column;
  line-height: 1.4;
}
.muted {
  color: var(--ac-text-subtle);
  font-size: 12px;
}
</style>
