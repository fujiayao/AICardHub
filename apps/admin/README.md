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

设置采用非敏感键白名单，不读取/回填/提交密钥或掩码，不展示原始审计 detail。图片使用已有公开 URL，不假装支持上传。

C8 物理 NFC 管理延期。知识批量上传、格式校验、评测、Excel 导入、来源分布、员工排行等未冻结接口功能明确标在页面。没有 mock 登录、假数据或无效操作按钮。

前端可独立检查；全仓检查入口由主线程维护 `scripts/check.ps1`，需要先集成其他所有者成果。

当前设置接口只持久化配置表，后端运行参数仍由环境读取；页面明确提示不保证立即生效，运行时应用待后端接入。
