<!-- 原型: B10 客户列表 -->
<script setup lang="ts">
import { shallowRef } from 'vue'
import { useRoute } from 'vue-router'
import CustomerList from '@/components/staff/CustomerList.vue'
import StaffShell from '@/components/staff/StaffShell.vue'
const route = useRoute(); const kind = shallowRef<'leads' | 'visitors'>(route.query.tab === 'visitors' ? 'visitors' : 'leads')
</script>
<template><StaffShell title="客户"><div class="cust-seg"><button type="button" :class="{ on: kind === 'leads' }" @click="kind = 'leads'">线索</button><button type="button" :class="{ on: kind === 'visitors' }" @click="kind = 'visitors'">访客</button></div><CustomerList :kind="kind" /></StaffShell></template>
<style scoped>
.cust-seg{display:flex;background:var(--c-seg-track);border-radius:10px;padding:3px;margin:0 0 var(--sp-3)}
.cust-seg button{flex:1;height:32px;border:0;border-radius:8px;background:transparent;font-size:var(--fs-sm);color:var(--c-text-2)}
.cust-seg button.on{background:var(--c-surface);color:var(--c-ink);font-weight:600;box-shadow:var(--sh-soft)}
</style>
