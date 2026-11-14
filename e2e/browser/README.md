# 独立浏览器验收 runner

只验证真实服务与页面，不实现业务、不替换接口、不修改 `e2e/local_acceptance.py`。对应 T42/T50；当前交付是可运行的 runner 与待联调用例，不代表 T42/T50 或 G3 通过。

## 准备与执行（PowerShell）

```powershell
Set-Location 'D:/AIWork/智能名片/AICardHub/e2e/browser'
pnpm install --frozen-lockfile --ignore-scripts
pnpm check
pnpm test:list
pnpm test:runner
```

`test:runner` 不要求业务服务或 seed，使用本机 Chrome/Edge 或已有 Playwright 缓存，不下载浏览器。支持 `PLAYWRIGHT_CHANNEL`、`PLAYWRIGHT_EXECUTABLE_PATH` 指定现有浏览器。

前端合并后，由主线程启动真实 MySQL/API/H5/admin，并在 `server` 执行 `uv run python -m app.seed`。本 runner 不自动启动、迁移、重置或 seed 数据库。后端必须实际使用 FakeLLM；确认后执行：

```powershell
$env:AICARD_LLM_MODE = 'fake'
pnpm preflight
pnpm test
# 只跑某一部分（同样执行 readiness 依赖）
pnpm test:h5
pnpm test:admin
pnpm test:layout
```

`test:admin` 当前使用 `admin-only.config.mjs`，仅依赖API/后台，跑公司资料和员工创建/停用，不访问H5、不聊天；公开名片同步通过API验证，员工只核验初始登录强制改密标记。完整原admin集成链路（H5公司展示、员工实际改密、A4画面）保持在 `pnpm test:admin-integrated`，需要两个前端均就绪。两者结果必须分别报告，后台独立检查不替代完整集成验收。

默认 H5 `http://127.0.0.1:5173`、API `http://127.0.0.1:8000`、后台 `http://127.0.0.1:5174`。可用 `AICARD_H5_URL`、`AICARD_API_URL`、`AICARD_ADMIN_URL` 覆盖；API 填 origin，不附 `/api/v1`。`AICARD_CARD_CODE` 默认 `demo`（冻结 seed 约定，替代旧 T42 的 `sk0001`）。`AICARD_CREDENTIALS` 默认读取仓库下 `server/local-credentials.json`，支持绝对路径或仓库相对路径；格式为 `admin/employee/colleague` 各含 `phone/password`。不得提交、复制或打印这个文件。

readiness 依赖要求三个服务均就绪，检查 health、HTML 和公开名片字段；HTTP 200 不代表页面业务通过。`AICARD_LLM_MODE=fake` 是操作者声明，服务端真实配置须由主线程核验。引导问题另断言 `done.model=本地演示模型` 且多个delta；纯手机号后续问独立验证policy无知识分支（nokb=true、无伪造引用、诚实说明、lead_prompt、不自动建线索），不要求该分支也调用Fake。`streams.jsonl`只保留模型分类/delta数量/nokb/提示数量，不持久化聊天原文或请求体。若既定引导问题命中policy则需核对其合成公开批准夹具，不能与正确的手机号无知识分支混淆。

## 项目与数据影响

| 项目 | 执行内容 | 数据影响 |
|---|---|---|
| runner | 真实浏览器启动、错误观察器自检 | 无业务网络请求 |
| readiness | 服务/seed 前置检查 | 只读 |
| h5-390 | 访客→SSE→明确同意→站内信→已联系；员工改简介→访客可见→恢复 | 一条合成线索最终置 invalid；产生访问、会话、消息、通知和统计 |
| admin | 公司简介→访客可见→恢复；新建员工→首次改密→停用 | 每次完整运行只新建一名员工，最终停用；保留审计记录 |
| layout-360/430 | A1/A2、B1/B2/B3/B4/B5/B6/B8/B9/B10/B12/B13 主要页 | 无员工/公司/名片/线索/知识写入；允许登录、访客初始化、空会话与访问计时 |

单 worker、无自动重试。360/430 用独立 `layout.spec.mjs`，不会重复执行业务用例。布局用例观察请求，发现非白名单写入即失败；未拦截请求，不 mock 被测应用。已读上报等若由页面自动触发，目前也会失败，交由主线程评估实际页面行为后明确调整布局巡检方案。

修改名片和公司资料均使用 UI 完成写入与正常恢复，随后通过真实 API 验证；失败时用原字段快照做 API 恢复并核对。请对隔离的本地演示库执行，避免与人工或其他任务同时修改相同资料。合成线索归档无效、新员工停用；冻结契约没有删除线索/员工接口，不宣称数据零残留。中途强制终止进程可能绕过 finally，主线程需检查演示资料与合成账号。

## 证据与隐私

每次运行输出到 `artifacts/<时间-进程>/`，不与上次混用：

- `results.jsonl`：用例名、项目、状态、断言位置、耗时与错误数量。
- `runtime.jsonl`：每个业务/布局用例的 `console.error`、`console.warn`、`pageerror` 计数。error 或 pageerror 非零即失败，warning 如实记录。
- `evidence.jsonl`：原型编号、状态、截图路径、真实视口、溢出检测结果与采集时间。
- `screenshots/<项目>/A1-default-390x844-<用例标识>.png`：精确视口截图，同时保存 `-full.png` 长图。

trace、video、自动失败截图关闭；设置 `PLAYWRIGHT_NO_COPY_PROMPT=1` 关闭自动页面快照，`preserveOutput=never` 丢弃 Playwright 原生失败产物（包括自动生成的 error-context），手工证据写在原生 results 目录之外。密码填入异常替换成固定诊断，不传播包含 typed 值的调用日志。只使用定制 reporter，不存错误原文、调用日志、HTTP 头、请求体、typed 值或 storageState。所有密码输入（含带密码标签的输入）在手动截图时遮罩，登录页截图在输入凭据之前拍摄。合成密码在内存生成，不进持久化报告。不要启用 `DEBUG=pw:*`、`PWDEBUG` 或切换 HTML/JSON/JUnit reporter 后对真实凭据执行测试，以免 Playwright 动作日志带入输入值。

`console` 与 `pageerror` 监听覆盖主页面及显式新建的访客/员工 context，只保存数值；新开 popup 也会被观察。runner 第二项故意注入错误验证观察器，成功表示“观察器抓到了错误”，不是业务页面无错误。

当前没有截图基线，不能用无依据的像素容差刷绿。只对已经成功加载并断言过内容的页面采集截图；布局失败也保留真实截图供复核。根页面横向滚动和超出视口元素会失败；合法横滑/裁剪容器内部不按视口越界判断。文本截断、44px 点击区、tokens、长姓名与公司名、安全区和真实设备兼容仍需后续专项断言及人工审图。

## 合并后联调规则

定位器集中使用用户可见的 label、role 和名称。预期 `dialog` 有可访问名称，表单控件关联 label，操作有 `button`/`menuitem`/`radio`/`checkbox` 语义。路由以规范 `/staff/**` 与 `/card/:code`、`/chat/:code` 为准；若最终路由不同，主线程核实后在测试中明确改动。不得用 `.first()` 规避本应唯一的表单/提交按钮冲突，不使用 CSS 层级或 nth-child 匹配。

当前业务 DOM 尚未合并，因此文案/角色/首次改密入口、线索详情路由、后台菜单等都是待核对的测试契约。联调可以修正定位与契约已批准的差异，不能删除隐私同意、多 delta、模型标识、持久化、跨员工 404、恢复、错误守卫、溢出等断言。完整覆盖矩阵与缺口见 `tasks/reports/browser-plan.md`。

本次范围不允许改 `scripts/`，因此未接入 `scripts/check.sh --e2e`；主线程应在其拥有的检查脚本中调用本目录 `pnpm test` 并原样传播退出码。不得把仅 runner 自检通过写成业务验收通过。
