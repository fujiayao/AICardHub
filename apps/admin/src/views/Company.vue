<!-- C3 企业与产品 -->
<script setup lang="ts">
import { useTemplateRef } from "vue";
import CompanyForm from "@/components/company/CompanyForm.vue";
import CompanyList from "@/components/company/CompanyList.vue";
import ProductPanel from "@/components/company/ProductPanel.vue";
import PageHeader from "@/components/shared/PageHeader.vue";
const primary = useTemplateRef<InstanceType<typeof CompanyForm>>("primary");
const list = useTemplateRef<InstanceType<typeof CompanyList>>("list");
</script>
<template>
  <section class="page">
    <PageHeader
      title="企业与产品"
      desc="主公司信息与产品目录供主公司名片使用；任职公司供跨公司任职的名片使用。保存后访客端使用最新内容。"
    />
    <CompanyForm
      ref="primary"
      @saved="list?.load()"
    /><ProductPanel /><CompanyList
      ref="list"
      @primary-changed="primary?.refresh()"
    />
  </section>
</template>
