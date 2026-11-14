<script setup lang="ts">
import PageHeader from "@/components/shared/PageHeader.vue";
import PendingContract from "@/components/shared/PendingContract.vue";
const steps = [
  "创建活动：名称、时间、地点、关联名片与负责员工",
  "生成活动专属二维码 / 链接，访问与留资按活动归属",
  "活动期间查看签到、访问、对话与线索",
  "活动结束后归档，进入活动报表",
];
</script>
<template>
  <section class="page">
    <PageHeader title="活动管理" desc="展会、沙龙等线下活动的获客配置与跟踪。">
      <el-button type="primary" disabled title="等待后端活动契约"
        >新建活动</el-button
      >
    </PageHeader>
    <PendingContract
      title="活动管理接口尚未发布"
      reason="后端正在新增活动管理 schema 与 operation_id。契约发布并生成客户端前，本页不调用接口、不保存数据，也不展示示例活动。"
      :steps="steps"
    />
  </section>
</template>
