<script setup lang="ts">
defineProps<{ loading?: boolean, error?: string, empty?: boolean, emptyText?: string }>()
defineEmits<{ retry: [] }>()
</script>
<template>
 <div v-if="loading" class="panel" role="status" aria-label="正在加载"><van-skeleton title :row="4" /></div>
 <div v-else-if="error" class="panel stack" role="alert"><p class="error">{{ error }}</p><van-button plain @click="$emit('retry')">重试</van-button></div>
 <van-empty v-else-if="empty" :description="emptyText || '暂时没有内容'" />
 <slot v-else />
</template>
