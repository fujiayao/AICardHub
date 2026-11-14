# DeepSeek 契约复核：执行器就绪，上游映射阻塞

- 时间：2026-11-14，Asia/Shanghai。
- 状态：**未完成模型复核；无 DeepSeek 生成的测试建议，不作为契约验收通过。**
- 允许复核对象：`contracts/IMPLEMENTATION.md`；本轮没有向 DeepSeek 发送该文件，因用户要求工具闭环成功后才进行审查，而前置验证失败。
- 本报告由核查执行者整理真实证据，不冒充 DeepSeek 的审查输出。

## 已完成

1. 使用已安装的 DeepSeek Harness `0.2.2-rc.3` 官方 CLI。环境 `DSH_HOME` 隔离到 `.local/agents/dsh/home`，使用独立 `headless` profile 与显式 `--patch`，不覆盖 desktop/global。
2. 本机 help/schema 均最终成功，schema 包含 80 个定义；保存安装包相关 schema 声明、正式 headless help 和 JSON Schema。最初冷启动 help/schema 在 45 秒无输出后终止，后续恢复，无修改安装包。
3. 执行一次纯合成 Messages 探测，验证官方支持路径及参数：`POST http://127.0.0.1:3425/v1/messages`，模型 `liangkeai-gg-g/deepseek-v4.1-flash`，`max_tokens=2048`，非流式，提示只要求固定合成标记。
4. 执行一次有界 dsh 合成工具任务，cwd `.local/agents/dsh/scratch`，要求先 write `marker.txt` 再 read。期限 120 秒，实际 41.548 秒退出 1，无任务重试。

## 协议诊断与实际模型证据

| 项目 | 证据 |
|---|---|
| 总控先前 Chat Completions 探测 | `tasks/reports/model-generation-check.json`：同 DeepSeek 目录 ID 返回 400；本轮未修改该文件 |
| 本轮 Messages 探测 | 400，3.641 秒；`invalid_request_error` |
| 脱敏 message | `量惟中转国模: unknown provider for model cn/deepseek-v4.1-flash` |
| 实际执行器 | DeepSeek Harness 官方 headless CLI `0.2.2-rc.3` |
| 请求协议 | 原生 DeepSeek adapter 的 Anthropic Messages，经本机 Magpie loopback 转发 |
| 请求模型 | `liangkeai-gg-g/deepseek-v4.1-flash`；配置 thinking enabled、reasoning low、maxTokens 4096 |
| dsh session ID | `session-1307ab5d-4d5a-4b12-837c-13e841c4126c` |
| 执行器事件 | session → turn_start → step_start → step_end → turn_end(error) → final(error) |
| 执行器错误 | `INVALID_REQUEST`，status 400，同一 unknown provider message |
| 实际成功模型 | **无**，没有成功响应的 model/usage，不能证明上游实际执行了 DeepSeek 推理 |
| 工具执行 | **0 次**；首步模型请求失败，未生成 `marker.txt`，没有 read/write 成功回执 |
| 子代理 | 配置最多 1 个、深度 1；实际 0 个，未干扰主实现代理 |

两种协议的失败和本轮实际执行器错误一致，指向上游 `cn/deepseek-v4.1-flash` provider/model 映射无法解析；没有证据支持把此次错误归为 max_tokens 不足。未猜测替代模型别名，未改供应商配置，未进行盲重试。

## 配置与资料边界

- 所有 dsh home/profile/session/storage/tmp/user 数据均落在 `.local/agents/dsh/`。
- 不复制全局完整配置、真实凭据、desktop profile；只使用 loopback 可接受的非秘密应用标识。
- 关闭 shell/web/MCP 接入、自动仓库指令、skills 扫描、官方 session-log 附送、遥测、模型恢复重试、标题模型、后台 jobs、fork/workflow。
- 已准备 `readonly.patch.yml`，关闭 write/edit/apply_patch，供路由修复后契约审查使用；当前未执行。
- 未开发业务、未改根配置、未改契约、未改验收测试或四代理所有权文件。

## 证据位置与下一步

- `.local/agents/dsh/README.md`：隔离方式、配置边界、恢复条件。
- `.local/agents/dsh/home/profiles/headless/audit.patch.yml`：可审核项目配置。
- `.local/agents/dsh/evidence/protocol-probe.json`：允许保留的 HTTP code/message。
- `.local/agents/dsh/evidence/synthetic-tool-attempt1.stdout`：JSON 事件证据。
- `.local/agents/dsh/evidence/synthetic-tool-attempt1.json`：时限与退出状态。此早期记录 `started_at` 为采集结束时间；duration 是单调时钟测量值，未篡改原始证据。
- `.local/agents/dsh/evidence/schema-final.stdout`：成功生成的本机完整 JSON Schema。

需总控/用户先修复或确认上游 DeepSeek 模型映射。恢复后重新通过合成工具闭环，再仅用获准契约文本执行一次只读审查。本轮不硬耗、不用 GPT 输出代替 DeepSeek 审查。
