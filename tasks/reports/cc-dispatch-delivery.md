# Claude Code 默认 GPT 调度交付

2026-11-14，Asia/Shanghai。本报告区分执行器、模型、实际工具、落盘产物和验证结果；不以空 final 或退出码单独认定完成。

## 已合入 main 的提交

| 分支/worktree | 提交 | 范围 | 验证 |
|---|---|---|---|
| `cc-fix` | `77d77df25c95b2c9bd57b6ea738dcbdc82d52136` | 仅 `server/app/integrations/llm/client.py`、`server/tests/unit/test_llm.py` | CC 离线 pytest 138 passed / 4.41s；宿主在最终提交上再测 138 passed / 2.06s；ruff check/format 通过 |
| `cc-qa` | `467fd49383a223d1e7792aa67ed030a2938d827a` | `e2e/responses_acceptance.py` 与独立交付报告 | 宿主 py_compile、--help、离线掩码/配置分支检查通过；实际 API 未运行 |
| `cc-ui` | `d4d6b38b7e1e87fda9501b19f62124fd10e6a854` | 仅 `apps/h5/vite.config.ts` 与独立冷启动报告 | 使用的 24 个 Vant 样式入口及根路径均存在；最终 TS 配置语法错误 0；fresh dev 浏览器复测未执行 |

三个分支均以 `9f7fee0` 集成代码为基线；实现时未改主线程业务工作区。后由总控审核并合入 main，本次只读 Git 日志已确认：

| CC 原提交 | main 集成提交 |
|---|---|
| FIX `77d77df` | `2a76c41` |
| QA `467fd49` | `94afb25` |
| UI `d4d6b38` | `5b1c36f` |

上表原验证列保留交付时的独立检查事实；主线程合入后的验证另列于下节，不能把旧的“未执行”记录解释为主线程现在也未执行。

## 主线程集成验证结果与来源

以下测试结果由用户在本轮明确转述主线程实际运行结果，本调度者未重新执行，也未读取或复制浏览器完整产物：

- main Chat 单测：**138 passed / 1.87s**，ruff/mypy 全过；与上表 CC 与宿主独立测试分开记录。
- UI 预优化配置合入并热重启后，主线程 dev 的两个 H5 完整业务用例均通过，总用例耗时分别 **12.69s、8.89s**。这些是整条用例总时长，**12s 动作断言边界保持不变**，没有通过加超时让测试通过。
- 主线程生产 preview 对照：**6 项业务/布局＋1 项预检，共 7/7 passed**。
- 证据支持此次预构建配置在主线程实际验证中的效果；不外推成所有设备、每一种全新缓存状态或生产发布均已验收。最初定位依据仍是 QA 的 cold optimizeDeps 整页 reload 诊断，不能将其写成业务代码缺陷。
- 真实 Responses API 验收由主线程接续；本报告不把 Fake/dev/preview 结果算成真实模型通过，也不提前宣称 QA 黑盒脚本 real 阶段通过。

## 执行器和模型证据

先运行 Magpie `agents` 官方摘要，确认 Claude Code 当前默认 `gptpro/gpt-6.1-sol`。所有本报告任务均启动本机官方 Claude Code CLI，**没有传 `--model`**，没有切旧 Claude 品牌模型、没有改全局配置，继承本机正常连接/代理环境。仅显式关闭非必要 MCP 和 hooks，按各任务精确开放文件工具与离线测试命令。

CLI 初始化及 assistant 消息事件均记录模型 `gptpro/gpt-6.1-sol`；这是 CLI/网关回执模型标识，不声称独立验证供应商物理模型身份。

| 任务 | 用时/结果 | 工具调用统计（父任务事件） | 子代理 |
|---|---|---|---|
| A：只读审查 | 258.642 秒，exit 0 | Read 32、Glob 8、Grep 13、Agent 1、Write 1 | 1 个只读子代理启动成功，结果曾由主代理交叉核对 |
| B：黑盒脚本 | 300.509 秒含回收，超时、exit 1；脚本和报告已落盘 | Read 12、Glob 5、Grep 2、Write 2、Agent 1、Edit 9 | 1 个只读子代理启动成功；到限前未确认完整收尾，不记完整完成 |
| FIX：终态修复 | 236.018 秒，exit 0 | Read 13、Glob 2、Grep 1、Agent 1、Edit 6、Bash 7 | 1 个测试子代理启动成功；父任务与子任务测试所有权并非从头完全互斥，最终文件经宿主统一检查 |
| UI：H5 冷启动配置 | 145.946 秒，exit 0 | Read 19、Glob 7、Grep 3、Bash 3、Edit 2、Write 1 | 小任务不再递归委派 |

真实 Read 闭环：A 首次读取 scratch 合成文件，tool_result 返回 `CC_DEFAULT_GPT_READ_OK_20261114`，再成功读契约和 delivery/python-testing skills。B、FIX 同样有实际 Read/Edit/Write/Bash 事件。没有把模型路由当执行器。

A 的精确路径 Write 被 don't-ask 权限拒绝，宿主从事件中取出 **CC 原样生成的 Write 内容** 保存本地报告，没有用 GPT 自写内容替代。B 的两次 Write 和后续 Edit 实际成功，存在真实脚本产物。FIX 的真实差异、命令回执和最终测试已另行核验。

CLI 报告成本：A 0.924553 美元，FIX 约 1.035829 美元；属于客户端 token 计价估算，不当作实际账单。B 超时没有完整 final 费用回执。任务均有 300 秒宿主上限，未使用续期。

## A 审查结论处置

1. **撤回第一条 P2。** 原报告把“主/备/兜底三个模型均原生 Responses”误读为“Responses 流式→非流式→ChatCompletions 协议降级”。用户未要求该功能，不实现非流式层或额外协议降级，不能据此阻塞产品。
2. 第二条 P2 有效：ChatCompletions adapter 未验证 finish_reason，截断/提前 EOF 可能被标成完成。由 CC-FIX 修复并验证，不影响已通过的 Responses 路径。

A 读源码期间主干从 d973cdc 更新到 9f7fee0，原稿明确了动态快照局限；正式处置以上述用户裁决与最终 FIX 代码为准，不把旧稿全文当最终验收结论。

## FIX 改动与验证

ChatCompletions 现在要求有非空字符串正文和正常 stop 终态；usage-only 空 choices 不当作终止。length、content_filter、未知/不支持终态、无成功终态 EOF、空完成均抛安全异常，不泄漏供应商文本。已经输出内容时由原 ChatEngine 返回 error，不进入备用/兜底或重放。首内容前失败仍可使用原主备机制。

最终提交仅两文件，合计 247 行新增、3 行删除。ResponsesLLMClient 的 AST 与基线相同，1024 输出上限和原生 Responses 行为未改。没有新增非流式实现。

离线覆盖 normal stop、同帧正文/终态、usage 空帧、length、content_filter、未知终态、缺 finish_reason、提前 EOF、内部标记部分输出不重放、200 字显示上限后仍校验终态等。

CC 真实命令回执：

```text
pytest tests/unit/test_llm.py -q -p no:cacheprovider
138 passed in 4.41s
ruff check --no-cache <两个文件绝对路径>
All checks passed!
ruff format --check --no-cache <两个文件绝对路径>
2 files already formatted
```

CC 曾在 cwd 改到 server 后使用仓库相对路径运行 ruff，得到 E902 路径不存在；随后改用绝对路径成功。报告保留失败事实，不将首次失败说成通过。宿主在最终提交独立运行同一 pytest 得 **138 passed in 2.06s**，并确认工作区无未提交改动。

## QA 脚本交接和限制

脚本由 CC 生成；因执行期间主干协议字段更新，宿主完成最小兼容校正：正式 `llm_api_mode`/fallback/tertiary 字段、第三 key 掩码、`--expect-mode real/fake`、主模型观测判据。报告明确标注“CC 生成、调度者校正”，不是纯 CC 已完成全部验证。

- real：不改运行配置、不强制 Fake，要求实际主模型 SSE 成功、合成资料引用与随机答案；只创建并清理自己登记 ID 的合成资料。
- fake：仅安全配置检查，不做真实模型声明、不创建资料/会话。
- 只在脚本运行时从指定忽略 credentials 文件解析登录信息，不读 `.env`，不输出账号/密码/token/key/错误正文。当前未运行 API，也未读取该 credentials。
- unknown 随机问题可能命中固定批准资料，非空 refs 不单独证明产品编造。严格用例不成立就报告失败/证据边界，不放宽断言冒充通过。
- 本轮只做 py_compile、--help 和小范围离线配置/掩码验证。主线程 Fake 阶段不切模式；后续真实 Responses 阶段由总控运行实际 API 验收。

运行示例在 cc-qa 工作区（报告输出需使用新文件名）：

```powershell
& 'D:/AIWork/智能名片/AICardHub/server/.venv/Scripts/python.exe' e2e/responses_acceptance.py --expect-mode real --base-url http://127.0.0.1:8000 --credentials 'D:/AIWork/智能名片/AICardHub/server/local-credentials.json' --report tasks/reports/responses-real-run1.json
```

## 本地证据与后续安排

`.local/agents/cc-dispatch/` 保存任务规格、CLI JSONL、宿主时间/退出元数据和白名单统计；不整目录提交，不披露内部子代理 ID 或完整上下文。

根据后续新授权完成 CC-UI 有界小任务，仅处理 H5 Vite cold optimizeDeps 配置及独立报告，路径与 FIX/QA 分离。CC 读取 pnpm/vite/vue/vue-best-practices skills，根据实际 import、自动 resolver 与已安装模块声明，在 optimizeDeps.include 添加已使用的根入口及 24 个组件样式入口；未新增框架/依赖、不删 legacy、不启动服务、不增加超时、不改 12 秒断言。宿主核对最终入口全部存在并用已安装 TypeScript 验证配置语法。随后主线程完成 dev 与生产 preview 验证，结果及来源见上节；详细初始报告随 `cc-ui` 提交保留。

本轮最终收尾只更新本报告，没有重跑服务、测试或模型任务；进程只读核查未发现本轮 `stream-json`＋`dontAsk` 调度启动的 CC 任务遗留。**不再创建 Codex 或 CC 任务、不继续改工作区其他文件**。等待主线程真实 API 验收；只有出现新缺陷并获得后续任务指示时才修复，不设置后台等待脚本或自动重试。
