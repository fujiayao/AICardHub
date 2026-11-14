# 数科名片 H5

独立前端应用，来源和许可证见 TEMPLATE_SOURCE.md / LICENSE。Node 24.18、pnpm 11.25。

```powershell
pnpm install --frozen-lockfile --ignore-scripts
pnpm dev
pnpm typecheck
pnpm lint
pnpm test --run
pnpm build
```

打开 http://localhost:5173/card/demo 或 http://localhost:5173/login。后端需在 8000 运行并 seed；账号从本机未跟踪的 server/local-credentials.json 获取，不提交账号口令。

/api、/files 和精确 /c/ 短链代理到 8000，保留前缀。/card、/chat 保持前端文件路由。没有 Service Worker。

`pnpm generate:api` 默认读取根 contracts/openapi.json；也可 `pnpm generate:api <绝对路径或URL>`。生成器校验 OpenAPI、operationId、请求/响应/参数 schema 与 multipart；生成目录禁止手改。SSE 只经 src/api/sse.ts。

浏览器截图可复用主仓库 e2e/browser 已安装的 Playwright，设置 AICARD_BROWSER_PACKAGE 为其 package.json、AICARD_CREDENTIALS 为本地 seed 凭据路径，运行 `node scripts/capture-browser.mjs`。不安装额外浏览器、不记录密码和 token。独立业务验收由主仓库 e2e/browser runner 执行。

本地候选状态及实际证据见 reports/H5-CANDIDATE.md。

后续修复与专项证据见 reports/H5-FIX-01.md。`node scripts/stage-browser.mjs` 会创建独立合成员工，验证后停用；仅修改该合成账号，不修改 demo，生成状态、二维码与通知截图。
