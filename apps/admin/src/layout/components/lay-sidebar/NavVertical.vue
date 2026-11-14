<script setup lang="ts">
// Static grouped navigation adapted from the pure-admin-thin sidebar.
import { computed } from "vue";
import { useRoute } from "vue-router";
import { adminRoutes, navGroups } from "@/router/modules/admin";
import AppIcon from "@/components/shared/AppIcon.vue";
defineProps<{ collapse: boolean }>();
const emit = defineEmits<{ select: [] }>();
const route = useRoute();
const groups = computed(() =>
  navGroups.map((name) => ({
    name,
    items: adminRoutes.filter((r) => r.meta?.group === name),
  })),
);
</script>
<template>
  <nav class="nav" aria-label="主导航">
    <div v-for="group in groups" :key="group.name" class="group">
      <p v-if="!collapse" class="group-title">{{ group.name }}</p>
      <ul>
        <li v-for="item in group.items" :key="item.path">
          <router-link
            :to="item.path"
            :class="['item', { active: route.path === item.path }]"
            :aria-current="route.path === item.path ? 'page' : undefined"
            :aria-label="collapse ? String(item.meta?.title) : undefined"
            :title="collapse ? String(item.meta?.title) : undefined"
            @click="emit('select')"
          >
            <AppIcon v-if="item.meta?.icon" :name="item.meta.icon" />
            <span v-if="!collapse" class="label">{{ item.meta?.title }}</span>
            <span v-if="!collapse && item.meta?.pending" class="badge"
              >待契约</span
            >
          </router-link>
        </li>
      </ul>
    </div>
  </nav>
</template>
<style scoped>
.nav {
  padding: var(--ac-space-2) var(--ac-space-3) var(--ac-space-5);
}
.group + .group {
  margin-top: var(--ac-space-3);
}
.group-title {
  margin: var(--ac-space-3) var(--ac-space-3) var(--ac-space-1);
  font-size: 12px;
  letter-spacing: 0.04em;
  color: var(--ac-on-navy-muted);
}
ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 2px;
}
.item {
  display: flex;
  align-items: center;
  gap: var(--ac-space-3);
  min-height: 40px;
  padding: 0 var(--ac-space-3);
  border-radius: var(--ac-radius-sm);
  color: var(--ac-on-navy-muted);
  text-decoration: none;
  font-size: 14px;
  transition:
    background-color 150ms ease,
    color 150ms ease;
}
.item:hover {
  background: var(--ac-navy-2);
  color: var(--ac-on-navy);
}
.item.active {
  background: var(--ac-primary);
  color: var(--ac-on-navy);
}
.item:focus-visible {
  outline-color: var(--ac-on-navy);
  outline-offset: -2px;
}
.label {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.badge {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 999px;
  border: 1px solid var(--ac-navy-3);
  color: var(--ac-on-navy-muted);
}
.item.active .badge {
  border-color: var(--ac-on-navy);
  color: var(--ac-on-navy);
}
</style>
