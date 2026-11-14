<script setup lang="ts">
import type { Campaign } from "@/api/schema";
import { formatTime, statusLabels, statusTagType } from "./campaignMeta";

defineProps<{ campaign: Campaign }>();
defineEmits<{ edit: []; report: [] }>();
</script>
<template>
  <div class="detail" aria-label="活动详情">
    <div class="tags">
      <el-tag :type="statusTagType[campaign.status]">{{
        statusLabels[campaign.status]
      }}</el-tag>
      <el-tag v-if="campaign.is_live" type="success" effect="dark">当前生效</el-tag>
      <el-tag v-else type="info" effect="plain">未在有效期</el-tag>
    </div>
    <el-descriptions :column="1" border>
      <el-descriptions-item label="活动名称">{{ campaign.name }}</el-descriptions-item>
      <el-descriptions-item label="开始时间">{{ formatTime(campaign.start_at) }}</el-descriptions-item>
      <el-descriptions-item label="结束时间">{{ formatTime(campaign.end_at) }}</el-descriptions-item>
      <el-descriptions-item label="展位">{{ campaign.booth || "—" }}</el-descriptions-item>
      <el-descriptions-item label="地点">{{ campaign.location || "—" }}</el-descriptions-item>
      <el-descriptions-item label="活动开场白">
        <span class="pre">{{ campaign.opening_override || "未设置（沿用名片 AI 模板）" }}</span>
      </el-descriptions-item>
      <el-descriptions-item label="活动引导问题">
        <ol v-if="campaign.guide_override.length" class="guides">
          <li v-for="(q, i) in campaign.guide_override" :key="i">{{ q }}</li>
        </ol>
        <span v-else>未设置（沿用名片 AI 模板）</span>
      </el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ formatTime(campaign.created_at) }}</el-descriptions-item>
      <el-descriptions-item label="更新时间">{{ formatTime(campaign.updated_at) }}</el-descriptions-item>
    </el-descriptions>
    <div class="actions">
      <el-button @click="$emit('report')">查看报表</el-button>
      <el-button type="primary" @click="$emit('edit')">编辑</el-button>
    </div>
  </div>
</template>
<style scoped>
.detail {
  display: flex;
  flex-direction: column;
  gap: var(--ac-space-3);
}
.tags {
  display: flex;
  gap: var(--ac-space-1);
  flex-wrap: wrap;
}
.pre {
  white-space: pre-wrap;
  word-break: break-word;
}
.guides {
  margin: 0;
  padding-left: 1.2em;
}
.actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--ac-space-2);
}
</style>
