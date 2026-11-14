# apps/admin/AGENTS.md —— 管理后台补充规则

- 基于 pure-admin-thin；路由为静态路由，菜单在 `src/router/modules/` 中定义
- 接口：`src/api/generated` + `src/api/adapters/`（把后端返回转换为模板组件需要的结构）；后端不为模板改接口格式
- 只用 Element Plus 与模板自带组件（@pureadmin/table 等）；不新增 UI 库
- Markdown 编辑用 md-editor-v3（T23/T38 引入，需在报告中注明）
- 样式不求精细，但表单校验、加载态、错误提示要完整
- 命令：`pnpm dev`、`pnpm lint`、`pnpm typecheck`、`pnpm build`
