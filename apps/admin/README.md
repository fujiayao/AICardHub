# 数科名片管理后台（本地候选）

基于官方 pure-admin-thin 6.2.0。来源、提交及保留文件见 [TEMPLATE_SOURCE.md](TEMPLATE_SOURCE.md)，许可证见 [LICENSE](LICENSE)。不是全量一期交付。

```powershell
pnpm install --frozen-lockfile
pnpm gen:api
pnpm dev
pnpm lint
pnpm typecheck
pnpm build
pnpm test
```

开发地址 `http://127.0.0.1:5174/`。代理 `/api` 到 `http://127.0.0.1:8000`，保留前缀。

生产默认 base 为 `/admin/`，路由 history 同步读取 Vite BASE_URL；反向代理需将 `/admin/*` 页面导航回退至 `/admin/index.html`。可用未跟踪环境变量 `VITE_BASE=/其他路径/` 覆盖；开发默认根路径。

`gen:api` 默认读取仓库 `contracts/openapi.json`，也接受参数或 `OPENAPI_SOURCE`（本地路径或真实后端 OpenAPI URL）。例如本工作区内：

```powershell
pnpm gen:api ../../../backend/contracts/openapi.json
```

也可传绝对路径。生成器校验必需后台接口与稳定 operation_id，然后从真实 schema 生成 paths/types 和经统一 client 发送的函数。生成文件附源 SHA256，不允许手改；无真实输入即报错，不制作假 OpenAPI。src/api/schema.ts 只导出真实生成模型的别名，所有适配器通过 generated 函数调用接口。

管理员只调用管理员登录入口，sessionStorage 使用 `aicardhub.admin.session.v1`，与 H5 的访客/员工存储隔离。JWT 到期和401退出；不调用 refresh token。首次改密有路由限制。管理员权限最终由后端验证。

设置采用固定键白名单，密钥状态仅转成已配置标记；不回填原值或掩码，空输入不提交覆盖，清空必须显式确认，不展示原始审计 detail。图片使用已有公开 URL，不假装支持上传。

C8 物理 NFC 管理延期。知识文件夹递归导入、评测、来源分布、员工排行等未冻结接口功能明确标在页面。没有 mock 登录、假数据或无效操作按钮。

前端可独立检查；全仓检查入口由主线程维护 `scripts/check.ps1`，需要先集成其他所有者成果。

运行时配置使用真实 `GET /api/v1/admin/runtime-settings` 和逐项 `PUT /admin/settings/{key}`。限额单位是每日对话次数，敏感词与主备模型从后续请求应用；保留天数由清理任务使用。切换真实模型前先逐项保存地址、名称、密钥；没有多项原子保存。`inline_token_limit` 目前不支持。

本轮修复提供可复用浏览器检查：`scripts/browser-knowledge-fix.mjs`（真实知识草稿/发布/撤回/删除及SSE检索引用、个人scope、合成资料清理、外部资源请求拦截）和 `scripts/browser-layout-fix.mjs`（390×844、桌面折叠菜单、生产/admin静态资源与深链刷新）。通过 `PLAYWRIGHT_MODULE` 指定已安装Playwright入口，`ADMIN_CREDENTIALS` 指向本地未跟踪seed凭据，脚本不输出口令。`ADMIN_URL` 可切换知识检查的根路径与生产子路径。

应用 `.prettierrc.json` 使用 `endOfLine: auto` 兼容 Windows 的 CRLF checkout。`gen:api` 使用同一配置格式化真实生成文件；不忽略格式检查文件。

员工导入支持后端规定的xlsx表头与逐行结果；Markdown批量上传只生成预览，每篇确认才保存成未公开、未批准草稿。合成浏览器导入检查前可运行 `python scripts/create-import-fixture.py`，文件在应用忽略目录`.local`内，初始密码随机生成且不输出。随后运行 `browser-import-fix.mjs`。运行时检查 `browser-runtime-fix.mjs` 只在Fake且主密钥未配置的本地环境执行，finally恢复敏感词/限额并清除合成密钥；不调用真实模型。

协议与三级模型：固定字段支持主模型/备用/兜底各自的 `*_api_mode`（`responses` / `chat_completions`）及后两级启用开关。界面仅读取后端返回的非敏感地址/型号/协议及密钥配置状态，不硬编码产品供应商、模型名或地址。备用仅在首段内容前失败切换，已输出后不重放。实际运行接口未返回的字段不显示，防止旧服务出现无效按钮。`browser-protocol-synthetic.mjs` 是拦截全部API的纯合成UI检查，不读本地凭据、不改后端配置、不调用真实模型；此证据不代表真实Responses生成已通过。
