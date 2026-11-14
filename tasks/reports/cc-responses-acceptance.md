# 任务 B：Responses 独立人工黑盒验收脚本

## 交付内容

- 基线：用户指定 `d973cdc`，独立 `cc-qa` worktree；未执行 Git 命令、未提交。
- 仅创建 `e2e/responses_acceptance.py` 与本报告；不修改业务、配置、单测、凭据或依赖。
- 使用已有 `httpx` 和标准库，不导入应用配置、不读取 `.env`。本轮未读取真实凭据。
- CLI：`--base-url` 默认 `http://127.0.0.1:8000`，仅接受数值 loopback HTTP(S) origin；`--credentials` 默认当前仓库 `server/local-credentials.json`；`--report` 指定新的脱敏 JSON 文件。
- 运行时仅在内存解析管理员/员工的 phone/password 并登录；不输出账号、口令、token、请求头、响应正文或异常正文。
- 禁用环境代理、重定向和 HTTP 重试；单普通请求总限时 15 秒、SSE 55 秒、工作阶段 150 秒、清理阶段 20 秒、异步外层 175 秒，为 180 秒预算预留报告写入时间。响应最多 2 MiB。
- 检查 health、runtime-settings 和两个密钥的独立 GET 返回；密钥只能为空或完整掩码。模式非真实、协议未显式声明 Responses 均不通过；不修改模型/协议/key，不切 Fake。
- 通过实际管理 API 创建唯一随机合成资料（public/approved=true），立即登记返回 ID；独立合成访客与 demo 名片创建会话；不读取已有业务资料全文，不创建线索。
- 读取 SSE 到正常 EOF，验证媒体类型、完整帧、非空 delta、恰好一个且末尾的 done、无 error、结构有效、真实已配置模型；还要求回答包含随机校验值，kb_refs 含自建资料 ID，nokb=false。
- 用全新随机标识、另一独立访客和会话检查无资料回答：nokb=true、refs=[]、有诚实拒答文本且未复述合成答案。该控制允许 model=policy；policy 从不作为真实模型生成通过依据。
- finally 仅 DELETE 本轮创建且已登记 ID 的资料，再 GET 确认 404。失败、超时、清理失败均脱敏记录并退出非零；报告原子写入，拒绝覆盖已有报告或凭据文件。

## 运行命令（交由主线程）

在 `D:\AIWork\智能名片\worktrees\cc-qa` 执行；使用已安装现有项目依赖的 Python：

```powershell
python -c "import ast; from pathlib import Path; ast.parse(Path('e2e/responses_acceptance.py').read_text(encoding='utf-8')); print('syntax ok')"
python e2e/responses_acceptance.py --help
python e2e/responses_acceptance.py --base-url http://127.0.0.1:8000 --credentials 'D:\AIWork\智能名片\server\local-credentials.json' --report tasks/reports/responses-acceptance-run1.json
```

跨 worktree 时由主线程将 `--credentials` 替换为实际主仓路径，不复制凭据。`--report` 必须使用不存在的新文件名。退出码 0 仅表示全部检查和清理成功；blocked/fail 均退出 1。

## 已知限制与待测

- **实际 API、编译/help、check.sh：未执行。没有真实模型验收通过结果。** 本轮无 shell 工具；主线程可使用上面的语法检查/help/API 命令，完整项目检查下一步命令为 `bash scripts/check.sh`。
- 已读基线 `runtime_settings.py` / LLM client 仅有 Chat Completions 实现。脚本不据此判定运行服务版本，而 GET 运行中配置；目前只接受明确字段 `llm_protocol=responses`。开启备援时还需 `llm_fallback_protocol=responses`，否则 blocked。最终实现若采用其他字段名，须基于最终契约调整检测，不能推断或伪造通过。
- 配置声明加真实生成不等于抓包证明供应商上游一定使用 Responses；本脚本不连接供应商、不探测 key，不声称覆盖真实上游 wire 协议。
- 随机无资料问题可能命中公司固定文档或其他资料；脚本仍严格要求 nokb/空 refs，不清空知识库、不改业务规避。失败表示本次无资料判据未成立，不直接断言供应商故障。拒答文本为明确词组启发式，不是完整语义证明。
- demo 仅产生合成访客/会话；现有契约没有会话删除端点，因此保留这些会话，不删除他人资源。公开检索仍可能将系统选中的批准公开资料传入当前真实模型，这不是脚本主动读取既有文档全文。
- 创建请求已到服务端但响应丢失、返回 ID 不符合契约，可能留下无法确认归属的合成资料；脚本报错，不扫描或删除疑似他人资料。系统强制终止也可能中断清理。
- 外层时间约束覆盖异步 HTTP 流程；本机凭据/报告磁盘操作不是可取消的网络请求，异常慢磁盘/操作系统挂起不属于 Python 异步硬截止保证。
- 独立只读安全/SSE 审查已委派一次，结果待回传；尚未据此宣称通过。

## 执行记录

成功读取：根 AGENTS、contracts/IMPLEMENTATION、用户指定的 delivery/testing 两个 SKILL；e2e/local_acceptance；workspace 的 runtime_settings、router（相关段）、admin_router（相关段）、schemas（相关段）；LLM client/service。只读定位使用 Glob/Grep；未重复成功读取，未运行任何命令或 API。无数据库迁移、无接口变更。


## 调度者核对与最小兼容校正（非 CC 原始输出）

- CC 默认实际模型 `gptpro/gpt-6.1-sol`，没有 `--model`；Read/Write/Edit/子代理均有真实事件。B 在 300 秒到限时停止，脚本及本报告已落盘，子代理收尾未确认，不记为完整API验收通过。
- 执行中 cc-qa 已由调度者从 d973cdc 快进到集成的 9f7fee0；CC 先读到旧配置，原脚本误写 llm_protocol/llm_fallback_protocol。调度者根据正式源改为 llm_api_mode / llm_fallback_api_mode，并加入 llm_tertiary_api_mode 和第三密钥掩码检查；没有增加协议降级或非流式实现。
- 调度者新增 --expect-mode real/fake：real 必须观测到主模型成功，fallback/tertiary 成功不能冒充主模型；fake 仅检查安全配置，明确 scope=fake_configuration_only，不创建资料或会话、不调用模型。
- 查询只发送随机 ASCII nonce，避免无资料控制复用资料中的中文关键词而必然命中。依然不保证公司所有资料均无随机标识匹配，未成立就如实失败。
- 离线检查：AST 解析、--help、fake/real 合成配置分支、掩码接受/明文拒绝均通过；未运行实际API，以免干扰总控 Fake 阶段。
- 原报告运行示例 credentials 路径漏 AICardHub，正确主仓路径为 D:/AIWork/智能名片/AICardHub/server/local-credentials.json；不复制该文件。
- 当前命令（实际执行需总控安排阶段）：

```powershell
& 'D:/AIWork/智能名片/AICardHub/server/.venv/Scripts/python.exe' e2e/responses_acceptance.py --expect-mode real --base-url http://127.0.0.1:8000 --credentials 'D:/AIWork/智能名片/AICardHub/server/local-credentials.json' --report tasks/reports/responses-real-run1.json
```

本文件保留上文 CC 原始记录以显示实际来源与局限；冲突处以上述已核对的兼容校正为准。


### 最终交接补充

- 用户已澄清三级指主/备/兜底三个模型均原生 Responses，不要求协议降级。脚本检查正式 api_mode 字段，不新增非流式层。
- 随机 unknown 问题可能检索到固定资料；refs 非空并不单独证明产品编造。脚本保留严格用例失败并明确错误码 no_knowledge_honesty_unproven_or_unrelated_retrieval，不放宽成通过；主线程需结合实际证据判定产品行为。
- 调度者真实执行 py_compile（字节码输出到外部临时目录）和 --help 均通过；未发实际 API、未读取 credentials。
- 脚本源为 CC 实际 Write/Edit 产物，字段/阶段兼容校正由调度者完成并如实标注，没有把CC超时或空final记成成功。
