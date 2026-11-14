<!-- C8 范围说明：独立物理 NFC 管理暂缓（postponed） -->
<script setup lang="ts">
import PageHeader from "@/components/shared/PageHeader.vue";
</script>
<template>
  <section class="page">
    <PageHeader
      title="交付范围 / NFC"
      desc="说明本地候选已交付与暂缓的能力，避免把未交付功能当作已完成。"
    />
    <div class="panel">
      <div class="panel-head">
        <h2>独立物理 NFC 卡管理</h2>
        <el-tag type="warning">暂缓</el-tag>
      </div>
      <p>
        当前仅使用员工固定名片短链进行本地验证。物理卡登记、绑定、解绑、挂失和换人重新绑定尚未交付。
      </p>
      <p>本地候选不提供上述操作入口，也不会把修改员工名片当成物理卡管理。</p>
    </div>
    <div class="panel">
      <div class="panel-head">
        <h2>后续原计划功能</h2>
        <el-tag type="info">待交付</el-tag>
      </div>
      <p>
        已提供员工Excel逐行导入与批量Markdown解析预览入口。文件夹递归导入、评测运行、产品配图上传及排序、来源分布与员工排行仍待交付。
      </p>
      <p class="muted">
        本地候选不代表完成原计划全量一期，也不代表真实模型评测或一周灰度通过。
      </p>
    </div>
  </section>
</template>
