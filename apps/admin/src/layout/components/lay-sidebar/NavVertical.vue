<script setup lang="ts">
// Static navigation adapted from the official pure-admin-thin sidebar.
import { useRoute } from "vue-router";
import { adminRoutes } from "@/router/modules/admin";
defineProps<{ collapse: boolean }>();
defineEmits<{ select: [] }>();
const route = useRoute();
</script>
<template>
  <el-menu
    router
    :default-active="route.path"
    :collapse="collapse"
    :collapse-transition="false"
    class="menu"
    @select="$emit('select')"
    ><el-menu-item
      v-for="item in adminRoutes"
      :key="item.path"
      :index="item.path"
      :aria-label="String(item.meta?.title)"
      ><span v-if="collapse" class="compact-label" aria-hidden="true">{{
        String(item.meta?.title).slice(0, 2)
      }}</span
      ><template #title
        ><span>{{ item.meta?.title }}</span></template
      ></el-menu-item
    ></el-menu
  >
</template>
<style scoped>
.menu {
  border: 0;
}
.compact-label {
  display: block;
  font-size: 13px;
}
</style>
