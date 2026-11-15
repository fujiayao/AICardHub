# AICardHub NFC 独立 QA 与回归计划

日期：2026-11-15  
工作区：`D:/AIWork/智能名片/worktrees/nfc-implementation`  
分支：`feat/nfc-implementation`  
基线提交：`d9014ad0cbe0b61a4f872ed6271f38765d864a9c`  
QA 写权限：仅 `tasks/reports/nfc/qa*.md`

## 1. 本轮状态与边界

本轮只完成规则核对、现有测试设施盘点、环境探测和可执行回归计划，没有修改产品代码、其他 agent 的测试或验收文件，也没有 commit。

开工时工作区仅有 `?? apps/nfc-android/`；该目录当时只有 Android agent 的 `.agent-marker`，尚无可审查源码或构建文件。报告本身会在生成后显示为新的未跟踪 QA 文件。后端和 Android 仍在实现，因此本轮不能给实现质量结论，也不能把任何 NFC 能力标成 `software_done` 或 `accepted`。

已阅读并与本计划对齐：

- `AGENTS.md`、`server/AGENTS.md`
- `docs/工程框架方案.md`
- `docs/adr/ADR-002-本地开发与验收执行.md`
- `docs/adr/ADR-005-原生部署与完整数据迁移.md`
- `docs/adr/ADR-006-手机NFC分享与双端兼容.md`
- `docs/NFC手机名片接入与功能补充方案.md`
- `tasks/nfc/README.md`
- `tasks/nfc/角色任务卡.md`
- `tasks/nfc/贴纸写入与采购验收.md`
- `tasks/nfc/验收与交付模板.md`
- `tasks/nfc/总控启动词.md`

## 2. 当前环境实测

| 项目 | 实测结果 | QA 判断 |
| --- | --- | --- |
| Magpie | `GET http://127.0.0.1:3425/v1/models` 返回 200，12 个模型 ID；含 `auto/deepseek-v4.1-flash` | 只读探针通过；模型目录存在不等于生成或工具循环已验证 |
| 主仓依赖 | `AICardHub/server/.venv`、H5/admin/e2e 的 `node_modules` 均存在 | 可复用主仓缓存，但测试必须在当前分支代码上执行 |
| 当前 worktree 依赖 | `server/.venv`、各 `node_modules`、`server/.env` 均不存在 | 开始实现审查前需按冻结依赖引导，或在总控指定环境中运行 |
| Python | 主仓 `.venv` 为 Python `3.12.12` | 架构兼容 |
| uv | PATH 中无 `uv`；`C:/Users/Administrator/.local/bin/uv.exe` 存在，版本 `0.12.20` | 使用脚本现有的绝对路径回退，不假设 PATH |
| Node/pnpm | Node `v24.18.1`，pnpm `11.25.0` | 满足当前 H5/admin 的版本要求 |
| Java | `JAVA_HOME=C:/Program Files/Java/jdk-21.0.12`；Java/Javac 均为 `21.0.12` | JDK 可用；是否匹配 Android Gradle Plugin 待 Android owner 冻结后确认 |
| Android 构建工具 | 未找到 Gradle、`adb`、`ANDROID_HOME`、`ANDROID_SDK_ROOT` 或默认 Android SDK | APK/仪器测试当前为 `awaiting_toolchain`，不能报告可构建 |
| MySQL | `MySQL80` 服务状态为 `Stopped`，`127.0.0.1:3306` 未监听；尝试启动返回无法访问服务 | 数据库当前不可用；真实 MySQL 接口测试暂不可执行 |
| 数据库标识 | 主仓配置仅核验为本地 `mysql+asyncmy` 的 `aicardhub` 与 `aicardhub_test`，端口 3306；未输出凭据 | 测试夹具要求数据库名必须为 `aicardhub_test` |

只读工具闭环记录使用以下固定探针，未使用密钥、员工资料或私有知识：

```powershell
$probe = Invoke-RestMethod -Uri 'http://127.0.0.1:3425/v1/models' -Method Get -TimeoutSec 10
[pscustomobject]@{ count = $probe.data.Count; ids = $probe.data.id } | ConvertTo-Json -Depth 4
```

应记录首次探针时间、执行器、模型 ID、退出码和耗时；后续若 `auto/deepseek-v4.1-flash` 实际生成失败，只能记录失败并切换已验证路由，不能由模型目录推断可用。

## 3. 现有检查设施与门禁覆盖

| 入口 | 当前行为 | NFC review 用法 |
| --- | --- | --- |
| `scripts/check.ps1` | 契约、ruff、格式、mypy、pytest、alembic heads、H5/admin lint/typecheck/build、H5 test；E2E 为显式开关 | 软件总门禁。需先恢复 MySQL、引导 worktree 依赖 |
| `scripts/check.sh` | 同等后端/frontend 检查；`--e2e` 直接跑本地与浏览器验收 | Windows 以 PowerShell 入口为准，避免模型模式与环境差异 |
| `scripts/check-contract.py` | 校验 operationId、成功响应和最小接口面，并写 `tasks/reports/contract-check.json` | 会写 QA 权限外文件；由总控运行。QA 只读时直接解析 OpenAPI 和记录 SHA-256 |
| `scripts/gen-api.ps1` | 导出 OpenAPI 并生成 H5/admin 客户端 | 会改契约与 generated；不能作为纯只读检查 |
| `server/tests/api/test_backend_isolation.py` | 真实 MySQL 夹具，强制 `aicardhub_test`，创建合成员工并清理已知 ID | NFC 接口测试可复用，但不得改其断言 |
| `server/tests/unit/test_root_path.py` | 已有根路径规范化和 `/c/{code}` 外部参数丢弃回归 | 冻结后必须新增 `Cache-Control: no-store` 断言 |
| `apps/h5` | Vitest：路径、平台、来源、SSE 等；`pnpm test` | 新增 NFC 路径/平台/来源测试必须进入同一套件 |
| `apps/admin` | 有 `pnpm test`，但 `check.ps1` 当前未调用 admin test | review 时单独执行，避免将其漏掉 |
| `e2e/browser` | Playwright 需要显式 E2E，且服务必须使用 fake 模型 | 可验页面/备用路径，不能替代 NFC 射频或标签回读 |

## 4. 机器可执行回归顺序

以下命令在依赖和数据库就绪后从 worktree 根目录执行。任何一步失败即保留真实输出，不把后续未运行项写成通过。

### 4.1 只读快照

```powershell
git status --short --branch
git rev-parse HEAD
git diff --stat d9014ad...HEAD
$schema = Get-Content -Raw contracts/openapi.json | ConvertFrom-Json
(Get-FileHash contracts/openapi.json -Algorithm SHA256).Hash.ToLowerInvariant()
$op = $schema.paths.'/api/v1/me/card/share-link'.get
$op.operationId
$op.responses.'200'.content.'application/json'.schema
git ls-files server/tests/acceptance
```

期望：基线/结果提交可追溯；operationId 为 `me_card_share_link`；响应字段及 required 与 `ShareLinkData` 冻结契约一致；验收测试未在本分支被修改。

### 4.2 依赖引导与后端聚焦回归

```powershell
$uv = "$env:USERPROFILE/.local/bin/uv.exe"
Push-Location server
& $uv sync --frozen
& $uv run python ../scripts/check-contract.py
& $uv run pytest -q tests/unit/test_root_path.py
& $uv run pytest -q tests/api -k "share_link or share or campaign or nfc"
& $uv run pytest -q
& $uv run ruff check app tests
& $uv run ruff format --check app tests
& $uv run mypy app
& $uv run alembic heads
Pop-Location
```

`check-contract.py` 会写非 QA 文件，执行前由总控明确所有者；若 QA 保持纯只读，则删除该行，改跑 4.1 的直接 OpenAPI 解析。真实 MySQL 测试不可用时应准确记录 `awaiting_database` 和失败类型，不以单元测试替代。

冻结接口至少覆盖：

| 用例 | 期望 |
| --- | --- |
| 员工 A 用自己的真实 token 请求 | 200，仅返回 A 的公开短链 |
| 员工 B 用自己的真实 token 请求 | 200，返回 B 自己的短链，不能串号 |
| 未登录、过期或无效 token | 401 |
| 请求夹带 `employee_id`、`card_id` 或任意 URL | 不得决定目标；未知参数按契约处理，不能让请求方指定域名 |
| `s=nfc` | 响应 source 为 `nfc`，短链包含受控 `s=nfc` |
| 缺省 `s` | 响应和短链为 `link` |
| 有效活动 `e` | 响应 `campaign_id` 与短链一致 |
| 过期、草稿、不存在或他人活动 | 按冻结契约拒绝或降级，不泄露活动私有内容 |
| 停用名片/停用员工 | 按冻结契约拒绝生成，不输出可继续访问的私有数据 |
| 根部署与 `/aicardhub/` | 前缀恰好一次，无绝对域名混拼、无开放跳转 |
| `/c/{code}` | 302 目的正确、保留 `s/e`、丢弃额外跳转参数、`Cache-Control` 含 `no-store` |
| 轻量接口不依赖媒体 | 字体/海报/二维码生成故障不影响获取短链 |

### 4.3 H5 与后台

```powershell
Push-Location apps/h5
pnpm test --run
pnpm lint
pnpm typecheck
pnpm build
Pop-Location

Push-Location apps/admin
pnpm test
pnpm lint
pnpm typecheck
pnpm build
Pop-Location
```

重点断言：NFC 使用 `s=nfc`、二维码使用 `s=qr`、普通分享使用 `s=link`；iOS 只展示接收说明；安卓未安装助手时有可操作备用路径；微信内失败不阻断复制和二维码；浏览器不伪报 NFC/HCE 硬件能力；`/share/nfc` 可打开，但普通 `/c/*` 不被 App Link 接管。

### 4.4 Android 构建与协议测试

Android owner 冻结 Gradle 输入并提供 wrapper 后执行等价命令：

```powershell
Push-Location apps/nfc-android
.\gradlew.bat test
.\gradlew.bat lint
.\gradlew.bat assembleDebug
Pop-Location
```

如设备已连接，另行只读记录：

```powershell
adb devices -l
adb shell getprop ro.build.version.sdk
adb shell pm list packages | Select-String '<冻结包名>'
```

当前缺 Android SDK/Gradle/adb，因此以上命令不能在本轮标成通过。仪器测试、HCE 射频和贴纸读写必须分别记录。

### 4.5 总门禁

```powershell
powershell -NoProfile -File scripts/check.ps1
powershell -NoProfile -File scripts/check.ps1 -E2E
```

仅在 fake 模型和本地服务 ready 后运行 E2E；真实模型/知识库评测另立报告。总门禁要求 MySQL、后端、H5、admin 和生成契约保持一致。

## 5. 三条验收链路与负例

### A. 安卓 HCE → 安卓/iPhone

1. 员工 H5 获取 `s=nfc` 短链，助手验证公开名片后才允许 emulate。
2. 接收机发现 URI，点击后到达受控短链和 H5。
3. 状态机 `emulate` 与 read/write/verify 互斥；退出 App、锁屏、超时、进程冷启动均关闭。
4. 读取成功后只能声称“标签/链接已被读取”，不能声称“对方已打开网页”或完成留资。

负例：NFC 关闭、不支持 HCE、其他钱包/HCE 冲突、接收机断网、证书错误、员工中途停用、活动过期、超长/分段 NDEF、读取中切换、进程被杀。

### B. 安卓写贴纸 → 回读

1. 显示员工、目标短链、已有 URI，用户确认后写。
2. 使用 `NdefMessage.toByteArray().size` 与 `getMaxSize()` 比较，不能按字符数。
3. 写后重连/回读，URI 与实际 NDEF 完全一致才成功。
4. 长期贴纸默认固定 HTTPS `/c/{code}?s=nfc`，默认无 `e`；临时活动 `e` 必须显示失效后果。

负例：只读、非 NDEF、容量不足、移开过早、写入失败、回读不一致、覆盖已有内容取消/失败、进程退出、模式冲突。V1 不提供锁卡；若未来出现锁卡入口，必须另有不可逆确认。

### C. 实体贴纸 → 安卓/iPhone → 短链/H5

1. 普通系统读取无需安装 AICardHub App。
2. 标准 NDEF HTTPS URI 打开受控短链，再进入 H5。
3. 读取、302、H5 访问、AI 对话、留资分别记录，不能相互替代。
4. 断网时区分“NDEF 已读取”和“网页不能加载”；恢复网络后重试。

负例：金属背板/抗金属不一致、无线充电区域、厚壳、天线方向、旧/新系统、过期活动、停用员工、标签批次差异。

## 6. 硬件与现场证据矩阵

所有未执行组合写 `awaiting_hardware`；二维码成功不能替代 NFC。

| 链路 | 最少证据 |
| --- | --- |
| 手机 HCE | 3 款支持 HCE 的安卓发送机 × 3 款安卓 + 3 款 iPhone 接收；每个声明支持的组合 20 次，记录成功率、点击/自动打开行为 |
| 写贴纸 | 每芯片型号/材质/批次至少 20 张；固定写入机也需跨至少 3 款安卓验证读取 |
| 实体贴纸 | 每批次至少 3 台安卓 + 3 台 iPhone；记录壳体、金属、无线充电位置、天线方向 |
| 失败复现 | 机型/系统/补丁、NFC 开关、锁屏状态、钱包/HCE、芯片型号/批次、目标 URI、实际 NDEF 字节数、失败步骤、截图/日志、下一定位点 |

## 7. 关键风险

1. **Android 尚不可构建。** 当前只有 marker，Gradle/adb/SDK 也未发现；必须先由 Android owner 冻结并提交 wrapper、SDK/AGP/依赖版本与许可证。
2. **真实数据库暂不可用。** MySQL80 停止且当前权限不能启动；接口 review 的授权隔离、活动状态和停用行为无法在本轮实测。
3. **worktree 无本地依赖与 `.env`。** 直接运行门禁会缺包；引导依赖或指定环境必须由总控协调，不能自行把主仓数据/密钥复制进新文件。
4. **检查脚本有副作用。** `check-contract.py` 会写报告，`gen-api` 会改契约/generated；QA 独占 `qa*.md`，只读 review 不自行运行这两个入口，除非总控明确指派。
5. **admin 自动测试未纳入主门禁。** `apps/admin/package.json` 有 `pnpm test`，但 `check.ps1` 当前只跑 lint/typecheck/build；QA 需单独执行。
6. **现有短链测试缺缓存约束。** 基线 `test_root_path.py` 尚未断言 `Cache-Control: no-store`；实现卡要求新增回归，不能只验证 302。
7. **硬件结论极易被软件证据夸大。** APDU/回读成功、短链 302、二维码分享和 H5 加载都不是最终射频兼容；必须持续分开状态。
8. **共享工作区存在并发变化。** 后端/Android 未冻结前只读快照可能快速过期；review 时以总控指定提交和 OpenAPI hash 为新基线，并重新读取 status/diff。

## 8. 后续 review 交付证据

总控重新唤醒后，QA 将针对指定已集成提交逐项填写：

- 基线、结果提交、OpenAPI SHA-256、变更 scope、未提交改动
- 原始文件 diff 和新增测试是否真正验证规则
- 每条执行命令、退出码、关键输出和未运行原因
- 接口隔离、URL/活动/停用、`no-store`、H5 source 和 Android 协议覆盖
- APK、手机射频、贴纸射频、部署各自状态
- `passed / changes_requested / awaiting_toolchain / awaiting_database / awaiting_hardware` 明确分类
- 每个失败项的现象、证据、两次尝试及下一定位点

本轮结论：QA 规划与入口已建立；软件实现尚未冻结，数据库与 Android 工具链不可执行，后续 review 等待总控指定提交与证据输入。
