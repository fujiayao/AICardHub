<script setup lang="ts">
import AppIcon from "@/components/shared/AppIcon.vue";
import type { NavIconName } from "@/router/modules/admin";
const links: { to: string; label: string; desc: string; icon: NavIconName }[] =
  [
    {
      to: "/employees",
      label: "员工与名片",
      desc: "新增员工、编辑名片",
      icon: "users",
    },
    {
      to: "/knowledge",
      label: "公开知识",
      desc: "上传与审核知识",
      icon: "book",
    },
    {
      to: "/templates",
      label: "AI 模板",
      desc: "维护助手话术模板",
      icon: "spark",
    },
    { to: "/issues", label: "问题池", desc: "处理未命中问题", icon: "alert" },
  ];
</script>
<template>
  <section class="panel" aria-labelledby="shortcut-title">
    <div class="panel-head"><h2 id="shortcut-title">快捷入口</h2></div>
    <ul class="links">
      <li v-for="l in links" :key="l.to">
        <router-link :to="l.to" class="link">
          <span class="ico"><AppIcon :name="l.icon" /></span>
          <span class="txt"
            ><strong>{{ l.label }}</strong
            ><small>{{ l.desc }}</small></span
          >
        </router-link>
      </li>
    </ul>
  </section>
</template>
<style scoped>
.links {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--ac-space-2);
}
.link {
  display: flex;
  gap: var(--ac-space-3);
  align-items: center;
  padding: var(--ac-space-3);
  border: 1px solid var(--ac-border);
  border-radius: var(--ac-radius-sm);
  color: var(--ac-text);
  text-decoration: none;
  transition:
    border-color 150ms ease,
    background-color 150ms ease;
}
.link:hover {
  border-color: var(--ac-primary);
  background: var(--ac-primary-soft);
}
.ico {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border-radius: var(--ac-radius-sm);
  background: var(--ac-primary-soft);
  color: var(--ac-primary);
}
.txt {
  display: grid;
  min-width: 0;
}
.txt strong {
  font-size: 14px;
}
.txt small {
  font-size: 12px;
  color: var(--ac-text-subtle);
}
</style>
