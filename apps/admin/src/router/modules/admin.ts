import type { RouteRecordRaw } from "vue-router";

export type NavIconName =
  | "dashboard"
  | "users"
  | "building"
  | "spark"
  | "rules"
  | "book"
  | "calendar"
  | "chart"
  | "alert"
  | "nfc"
  | "settings";

declare module "vue-router" {
  interface RouteMeta {
    title?: string;
    desc?: string;
    icon?: NavIconName;
    group?: string;
    pending?: boolean;
  }
}

export const navGroups = [
  "概览",
  "名片与企业",
  "AI 与知识",
  "获客运营",
  "系统",
];

export const adminRoutes: RouteRecordRaw[] = [
  {
    path: "/dashboard",
    name: "dashboard",
    component: () => import("@/views/Dashboard.vue"),
    meta: { title: "工作台", icon: "dashboard", group: "概览" },
  },
  {
    path: "/employees",
    name: "employees",
    component: () => import("@/views/Employees.vue"),
    meta: { title: "员工与名片", icon: "users", group: "名片与企业" },
  },
  {
    path: "/company",
    name: "company",
    component: () => import("@/views/Company.vue"),
    meta: { title: "企业与产品", icon: "building", group: "名片与企业" },
  },
  {
    path: "/templates",
    name: "templates",
    component: () => import("@/views/Templates.vue"),
    meta: { title: "AI 模板", icon: "spark", group: "AI 与知识" },
  },
  {
    path: "/knowledge",
    name: "knowledge",
    component: () => import("@/views/Knowledge.vue"),
    meta: { title: "公开知识", icon: "book", group: "AI 与知识" },
  },
  {
    path: "/rules",
    name: "rules",
    component: () => import("@/views/Rules.vue"),
    meta: { title: "回答规则", icon: "rules", group: "AI 与知识" },
  },
  {
    path: "/activities",
    name: "activities",
    component: () => import("@/views/Activities.vue"),
    meta: {
      title: "活动管理",
      icon: "calendar",
      group: "获客运营",
      pending: true,
    },
  },
  {
    path: "/reports",
    name: "reports",
    component: () => import("@/views/Reports.vue"),
    meta: {
      title: "活动报表",
      icon: "chart",
      group: "获客运营",
      pending: true,
    },
  },
  {
    path: "/issues",
    name: "issues",
    component: () => import("@/views/Issues.vue"),
    meta: { title: "问题池", icon: "alert", group: "获客运营" },
  },
  {
    path: "/scope",
    name: "scope",
    component: () => import("@/views/Scope.vue"),
    meta: { title: "交付范围 / NFC", icon: "nfc", group: "系统" },
  },
  {
    path: "/settings",
    name: "settings",
    component: () => import("@/views/Settings.vue"),
    meta: { title: "设置与审计", icon: "settings", group: "系统" },
  },
];
