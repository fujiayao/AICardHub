<!-- 原型: B10 客户列表 -->
<script setup lang="ts">
import { shallowRef } from 'vue'
import { useRoute } from 'vue-router'
import CustomerList from '@/components/staff/CustomerList.vue'
import StaffShell from '@/components/staff/StaffShell.vue'
const route = useRoute(); const kind = shallowRef<'leads' | 'visitors'>(route.query.tab === 'visitors' ? 'visitors' : 'leads')
</script>
<template><StaffShell title="客户"><van-tabs v-model:active="kind"><van-tab title="线索" name="leads" /><van-tab title="访客" name="visitors" /></van-tabs><CustomerList :kind="kind" /></StaffShell></template>
