# apps/h5/AGENTS.md —— H5 补充规则

> 在根目录 AGENTS.md 之后阅读。T08 审查后会补充“范本写法”。

- 页面在 `src/pages/`（文件路由），首行 `<!-- 原型: Bxx 页面名 -->`；照 `pages/card/[code].vue`（T07）写
- 组件：两端共用放 `components/common/`，访客专用 `components/visitor/`，员工专用 `components/staff/`；访客页不得 import staff
- 只用 `<script setup lang="ts">`；状态跨页面才放 Pinia
- 接口：`src/api/generated` 中的函数；SSE 只用 `src/api/sse.ts` / `useChatStream`
- 提示：`showToast` / `showDialog` / `showConfirmDialog`（Vant 4 写法）
- 样式：只用 `src/styles/tokens.css` 变量和 UnoCSS 主题类；禁止颜色字面量与任意值颜色；图标 `i-lucide-*`
- 环境：`src/platform/` 提供 isWechat、callPhone、saveContact、openMap、share、copyText
- 每个页面处理加载态、空状态、错误态
- 截图：390×844，保存到 `tasks/reports/screenshots/T{xx}/`，文件名带原型编号和状态
- 命令：`pnpm dev`、`pnpm lint --fix`、`pnpm typecheck`、`pnpm test`、`pnpm build`
