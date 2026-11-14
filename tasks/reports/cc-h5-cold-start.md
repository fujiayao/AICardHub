# H5 dev 冷启动小修

## 修改及理由

- 仅修改 `apps/h5/vite.config.ts`，新增 `optimizeDeps.include`；本文件为交付报告。未改业务、依赖、lock、QA、根配置或测试断言，未提交。
- QA 已确认（任务输入，本任务未复测）：fresh dev 按页面发现 Vant 自动导入，重新预构建触发整页 reload，打断点击；生产 dist 对照编辑 293ms、引导 1.485s，完整 Fake 通过。此次针对开发依赖发现，不调整业务或 12s 断言。
- 提前纳入实际源码运行时入口 `vue`、`vue-router`、`pinia`、`axios`、`vant`，以及自动 resolver 产生的 `vant/es`。
- `build/vite/index.ts` 使用默认 `VantResolver()`。已读安装版本 resolver 实现：组件从 `vant/es` 导入，副作用为 `vant/es/<组件>/style/index`。因此仅加入实际组件对应的样式 JS 入口，不猜测逐组件 JS 导入路径，不全量预构建所有 Vant 组件。
- 源码扫描未发现 `@vueuse/*` 导入，故不因 package 声明而加入。`vue-router/auto-routes` 是文件路由插件入口，不当作普通运行时包预构建。原有 `vant/lib/index.css` 保持不变，不将纯 CSS 加入 include。
- 不添加 `server.warmup`、`noDiscovery`、超时；保留 legacy、端口、代理及 build 配置。

## 实际扫描的组件与入口

扫描范围：`apps/h5/src` 的 Vue 相关 import、Vant import 及 `<van-…>` 使用；插件配置 `apps/h5/build/vite/index.ts`。

共 24 个实际使用的组件：

```text
badge button cell cell-group checkbox empty field form
list loading nav-bar overlay popup pull-refresh radio radio-group
search skeleton swipe-cell switch tab tabbar tabbar-item tabs
```

配置将上述名称映射为 `vant/es/${component}/style/index`；组件代码由共同的 `vant/es` 入口覆盖。`showToast`、`showConfirmDialog` 是源码从 `vant` 显式导入，已由 `vant` 入口覆盖，未虚构自动 API 样式导入。

## 静态核验

- 已用文件匹配确认主仓安装目录内上述 **24/24** 个 `vant/es/<组件>/style/index.mjs` 均存在，`vant/es/index.mjs` 存在。
- 已读 Vant 4.10.2 的 package：`module` 为 `es/index.mjs`，无 exports 限制；已读 field 样式入口，确认为导入 CSS 的 JS 模块。
- 已读主仓 Vue 3.5.45、Vue Router 5.5.0、Pinia 4.1.0、Axios 1.21.1 的公开 package，均声明所用根入口。
- 已读安装的 Vite 8.3.8 类型定义 `DepOptimizationConfig.include?: string[]`，支持强制预构建可解析入口；本次无需实验性 glob。
- 已执行命令 `git status --short; node --version`：初始工作区无改动，Node v24.18.1。
- 已执行 `git diff --check; git diff --stat; git status --short`：空白检查无报错，配置新增 12 行，工作区仅指定配置和本报告两处变更。
- Node 扫描/解析脚本被工具权限拒绝，未执行；随后通过专用 Read/Glob/Grep 完成上述文件级核对，没有安装或复制依赖。
- 配置语法执行验证：未执行。调度者可从本 worktree 运行以下只读 TypeScript 语法检查（使用主仓已安装工具，不加载 Vite 配置、不启动服务）：

```bash
node --input-type=module -e 'import fs from "node:fs"; import ts from "D:/AIWork/智能名片/AICardHub/apps/h5/node_modules/typescript/lib/typescript.js"; const p="apps/h5/vite.config.ts"; const r=ts.transpileModule(fs.readFileSync(p,"utf8"),{fileName:p,reportDiagnostics:true,compilerOptions:{target:ts.ScriptTarget.ESNext,module:ts.ModuleKind.ESNext}}); const errors=(r.diagnostics??[]).filter(d=>d.category===ts.DiagnosticCategory.Error); for(const d of errors) console.error(ts.flattenDiagnosticMessageText(d.messageText,"\n")); if(errors.length) process.exit(1); console.info("Vite config syntax OK");'
```

## 留主线程验证

调度者补充（非 CC 自报）：已用主仓安装的 TypeScript `transpileModule` 解析最终配置，错误数 **0**；并独立核对 24 个样式入口与 6 个根路径均存在。未启动浏览器或宣称 cold reload 已消失。CC 本任务默认模型回执 `gptpro/gpt-6.1-sol`，耗时 145.946 秒、exit 0；实际工具 Read 19、Glob 7、Grep 3、Bash 3、Edit 2、Write 1。两次工具错误已保留，其中一次 Node 扫描权限拒绝，不把它记为执行成功。

- typecheck/build、`scripts/check.sh`：未执行；worktree 未安装依赖，按任务约束不安装，不重跑 QA 大测试。
- fresh dev 浏览器复测、截图：未执行；尚未实证确认 reload 已消失，不将文件级核验表述为浏览器验证通过。
- 未启动服务，未占用 5173/5183。主线程继续使用既有 QA 流程验证 fresh dev 不再因这些入口新增预构建而 reload；可用独立 preview 5183 做最终完整 Fake E2E。保持原 12s 断言，无需加超时。
