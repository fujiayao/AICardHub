<script setup lang="ts">
defineProps<{ busy: boolean; error: string }>();
defineEmits<{ retry: [] }>();
</script>
<template>
  <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon
    ><el-button link type="primary" @click="$emit('retry')"
      >重试</el-button
    ></el-alert
  ><el-skeleton v-else-if="busy" :rows="4" animated />
</template>
