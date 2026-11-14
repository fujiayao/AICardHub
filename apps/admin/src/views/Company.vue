<!-- C3 企业与产品 -->
<script setup lang="ts">
import CompanyForm from "@/components/company/CompanyForm.vue";
import ProductPanel from "@/components/company/ProductPanel.vue";
</script>
<template>
  <section class="page">
    <div>
      <h1>企业与产品</h1>
      <p class="muted">
        所有名片共用公司信息。修改保存后，访客端使用最新内容。
      </p>
    </div>
    <CompanyForm /><ProductPanel />
  </section>
</template>
