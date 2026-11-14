<!-- C3 企业与产品 -->
<script setup lang="ts">
import CompanyForm from "@/components/company/CompanyForm.vue";
import ProductPanel from "@/components/company/ProductPanel.vue";
import PageHeader from "@/components/shared/PageHeader.vue";
</script>
<template>
  <section class="page">
    <PageHeader
      title="企业与产品"
      desc="所有名片共用公司信息。修改保存后，访客端使用最新内容。"
    />
    <CompanyForm /><ProductPanel />
  </section>
</template>
