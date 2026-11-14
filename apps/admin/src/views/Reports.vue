<script setup lang="ts">
import PageHeader from "@/components/shared/PageHeader.vue";
import PendingContract from "@/components/shared/PendingContract.vue";
const steps = [
  "按活动查看访问、独立访客、AI 对话与线索汇总",
  "按员工 / 名片拆分活动获客贡献",
  "线索跟进状态分布与超时未跟进提醒",
  "导出活动线索明细（需后端导出接口）",
];
</script>
<template>
  <section class="page">
    <PageHeader title="活动报表" desc="按活动汇总的获客与跟进结果。">
      <el-button disabled title="等待后端报表契约">导出报表</el-button>
    </PageHeader>
    <PendingContract
      title="活动报表接口尚未发布"
      reason="报表依赖后端活动统计契约。发布前本页不计算、不推测任何指标；工作台的近 7 天全局统计仍可正常使用。"
      :steps="steps"
    />
  </section>
</template>
