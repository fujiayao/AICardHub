<script setup lang="ts">
// Single inline SVG icon set (stroke icons); no second icon library.
import type { NavIconName } from "@/router/modules/admin";
defineProps<{
  name: NavIconName | "menu" | "collapse" | "logout" | "refresh";
}>();
const paths: Record<string, string[]> = {
  dashboard: ["M3 3h7v9H3z", "M14 3h7v5h-7z", "M14 12h7v9h-7z", "M3 16h7v5H3z"],
  users: [
    "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2",
    "M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
    "M22 21v-2a4 4 0 0 0-3-3.87",
    "M16 3.13a4 4 0 0 1 0 7.75",
  ],
  building: [
    "M4 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16",
    "M16 9h2a2 2 0 0 1 2 2v10",
    "M2 21h20",
    "M8 7h4M8 11h4M8 15h4",
  ],
  spark: [
    "M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z",
    "M19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8z",
  ],
  rules: ["M9 6h12", "M9 12h12", "M9 18h12", "M4 6h.01M4 12h.01M4 18h.01"],
  book: [
    "M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z",
    "M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5",
  ],
  calendar: ["M3 5h18v16H3z", "M16 3v4M8 3v4M3 10h18"],
  chart: ["M3 3v18h18", "M7 15l4-4 3 3 5-6"],
  alert: [
    "M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z",
    "M12 9v4M12 17h.01",
  ],
  nfc: [
    "M6 8.5a6 6 0 0 1 0 7",
    "M10 6a10 10 0 0 1 0 12",
    "M14 4a14 14 0 0 1 0 16",
  ],
  settings: [
    "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z",
    "M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-2.9-1.2l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1A1.7 1.7 0 0 0 3.1 14H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.2-2.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1A1.7 1.7 0 0 0 10 3.1V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 2.9 1.2l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0 1.2 2.9h.1a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z",
  ],
  menu: ["M3 6h18M3 12h18M3 18h18"],
  collapse: ["M3 4h18v16H3z", "M9 4v16", "M15 10l-2 2 2 2"],
  logout: [
    "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4",
    "M16 17l5-5-5-5",
    "M21 12H9",
  ],
  refresh: ["M21 12a9 9 0 1 1-3-6.7L21 8", "M21 3v5h-5"],
};
</script>
<template>
  <svg
    class="ac-icon"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <path v-for="d in paths[name]" :key="d" :d="d" />
  </svg>
</template>
<style scoped>
.ac-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}
</style>
