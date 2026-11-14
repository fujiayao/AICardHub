import type { RouteRecordRaw } from "vue-router";
export const adminRoutes: RouteRecordRaw[] = [
  {
    path: "/dashboard",
    name: "dashboard",
    component: () => import("@/views/Dashboard.vue"),
    meta: { title: "工作台" },
  },
  {
    path: "/company",
    name: "company",
    component: () => import("@/views/Company.vue"),
    meta: { title: "企业与产品" },
  },
  {
    path: "/templates",
    name: "templates",
    component: () => import("@/views/Templates.vue"),
    meta: { title: "AI 模板" },
  },
  {
    path: "/rules",
    name: "rules",
    component: () => import("@/views/Rules.vue"),
    meta: { title: "回答规则" },
  },
  {
    path: "/knowledge",
    name: "knowledge",
    component: () => import("@/views/Knowledge.vue"),
    meta: { title: "公开知识" },
  },
  {
    path: "/employees",
    name: "employees",
    component: () => import("@/views/Employees.vue"),
    meta: { title: "员工与名片" },
  },
  {
    path: "/scope",
    name: "scope",
    component: () => import("@/views/Scope.vue"),
    meta: { title: "交付范围 / NFC" },
  },
  {
    path: "/issues",
    name: "issues",
    component: () => import("@/views/Issues.vue"),
    meta: { title: "问题池" },
  },
  {
    path: "/settings",
    name: "settings",
    component: () => import("@/views/Settings.vue"),
    meta: { title: "设置与审计" },
  },
];
