<!-- C3 企业与产品 -->
<script setup lang="ts">
import CompanyForm from "@/components/company/CompanyForm.vue";
import CompanyList from "@/components/company/CompanyList.vue";
import ProductPanel from "@/components/company/ProductPanel.vue";
import PageHeader from "@/components/shared/PageHeader.vue";
</script>
<template>
  <section class="page">
    <PageHeader
      title="企业与产品"
      desc="主公司信息与产品目录供主公司名片使用；任职公司供跨公司任职的名片使用。保存后访客端使用最新内容。"
    />
    <CompanyForm /><ProductPanel /><CompanyList />
  </section>
</template>
