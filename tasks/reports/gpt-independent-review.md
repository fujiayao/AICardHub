# GPT 独立代码审查

2026-11-14，Asia/Shanghai。范围：server 鉴权、知识权限与流生命周期；只读审查，不修改业务代码。发现 **1 条 P1、3 条 P2**，均有独立合成复现。

## 范围与证据边界

- 基准候选：`4fbdf8239e660306fbafe2320340cfb63984d0f9`。
- 结束时主线程 HEAD 已推进至 `717dab06373a174314d0f752c2e25ab2007d2132`；本报告涉及的 `service.py`、`deps.py`、`kb/store.py`、`knowledge_service.py`、`chat_service.py` 在检查时与基准内容一致（忽略 CRLF/LF 差异）。行号按本轮读取的这些文件。
- 已沿实际 router → service → dependency/store 链路检查，并阅读相关 schema、错误处理、LLM 客户端与已有测试。
- 验证使用真实 FastAPI 应用路由、httpx ASGITransport、真实 bcrypt/JWT、真实 KnowledgeStore 文件/Git 修订与搜索。**数据库是明确的 MemorySession 替身，不是真实 MySQL或正在运行的 localhost 服务；流清理故障通过合成客户端注入。** 不将结果冒充生产端到端验收。
- 所有身份、密码、令牌、文档和上传字节均现场合成。`Settings(_env_file=None)` 且数据库指向未使用的假端点；未读取 `.env`、用户凭据、演示账号口令、真实知识或业务记录，没有外部模型调用。
- 未重复：通知 target 缺失、runtime 设置不生效、transfer 仅转线索、同会话 lease、原 jobs 缺失。这些已知修补不计入本报告。
- 本轮由当前 GPT 审查上下文独立完成；未创建新聊天、未调用 Claude/DeepSeek/Magpie，不干扰实现代理。

## 1. [P1] 回滚未批准的旧草稿会继承当前版本批准状态并立即公开

**位置：** [server/app/kb/store.py:333](../../server/app/kb/store.py#L333)，重点为 334–338 行。入口为 `knowledge_service.note_rollback`（126–136 行）及 `POST /api/v1/admin/kb/files/{file_id}/rollback`。

`rollback` 从历史取目标正文，却用当前版本的 `public`、`approved` 覆盖目标标记。当前版本公开批准并不证明另一份旧正文也已获批。该路径没有独立批准新 revision 的步骤，未批准的旧草稿因当前版本标记被直接用于访客检索。这与现有“撤回后回滚仍不公开”测试是相反方向，已有测试没有覆盖。

**合成复现：**

1. 管理员创建 r1，正文为合成标记 A，`public=false, approved=false`。
2. 更新为不同的合成正文 B，形成 r2，显式设 `public=true, approved=true`。
3. 仅调用 rollback `{revision:1}`。
4. 实际返回 r3，正文为 A，`public=true, approved=true`；真实 `store.search(A)` 返回该未批准正文。

创建、更新、回滚三个真实 ASGI HTTP 请求均返回 **200**。没有依赖伪造的历史文件或手改 frontmatter。

**最小修复方向：** 回滚生成新 revision 时清除批准状态，必要时同时清除公开状态；审批应明确绑定所恢复正文/revision。保留“已撤回内容不能因回滚重新公开”的现有保证，不直接改为盲目恢复历史旗标。

**回归：** 覆盖“旧草稿 → 当前公开批准 → 回滚草稿”和“当前撤回 → 回滚旧公开版本”，未经重新批准时搜索都必须排除。

## 2. [P2] 自行修改密码没有推进 token_version，旧会话持续有效

**位置：** [server/app/modules/workspace/service.py:66](../../server/app/modules/workspace/service.py#L66)，66–68 行；鉴权对应 [server/app/core/deps.py:29](../../server/app/core/deps.py#L29)。

自行改密仅更新 password_hash 和 must_change_pwd；既有 JWT 的 version 仍与员工记录一致。已泄漏或另一个终端保存的旧令牌可以继续访问员工接口。首次强制改密时尤其明显：同一初始密码签出的多个令牌不会随改密失效；`must_change_pwd=false` 后，这些旧令牌反而通过原先的访问限制。管理员重置密码已推进 version，自行改密遗漏了同一机制。

**合成复现：** 用 version=0 的合成员工令牌请求 `/api/v1/me/profile` 得 **200**；用该令牌向 `/api/v1/auth/change-password` 提交正确旧密码及新密码得 **200**；仍用原令牌再次请求 profile，实际仍为 **200**，记录的 token_version 仍为 **0**。验证运行真实 JWT 解码、bcrypt 校验、依赖和改密 service，员工存储为内存替身。

**最小修复方向：** 改密事务内递增 token_version，并让当前客户端重新登录，或明确返回本次改密后重签的令牌；不得仅修改前端本地 token。

**回归：** 同一账号两个实际签发 token，改密前有效；改密后旧 token 都返回 401，新密码登录后签发的新 token 正常。此建议需要补真实 MySQL/HTTP 复测，不把本轮内存验证当作已补齐。

## 3. [P2] 上传损坏 PDF 返回内部错误 500，而非可处理的输入错误

**位置：** [server/app/modules/workspace/knowledge_service.py:261](../../server/app/modules/workspace/knowledge_service.py#L261)，261–264 行；`extract_document` 在约 244 行调用 pymupdf.open。

导入只捕获 ValueError/UnicodeError。实际安装的 `pymupdf.FileDataError` 继承 RuntimeError，因此普通损坏 PDF 逃逸到全局 500 处理。用户选择了合法扩展名但文件损坏，就会被呈现为服务内部故障，而不是 422“文件无法解析”；这是输入边界的确定性缺口。

**合成复现：** 已鉴权合成员工向 `/api/v1/me/kb/import` 上传文件名 `synthetic-invalid.pdf`、内容为固定非 PDF 字节串。真实 multipart 路由/线程池/解析库返回 **500**，响应 code=`INTERNAL_ERROR`；内部异常类型为 FileDataError，未打印原始文件或凭据。

**最小修复方向：** 在解析适配层捕获 PDF/Word 库明确的文件解析异常并转为 AppError 422；对真正系统故障保持 500，避免无差别吞掉所有异常。

**回归：** 破损 PDF、空 PDF、破损 DOCX 均应返回可识别的 422；合法合成文档仍生成 draft，不直接发布。

## 4. [P2] 上游关闭异常会跳过流结果落库与 SSE 终止事件

**位置：** [server/app/modules/workspace/chat_service.py:198](../../server/app/modules/workspace/chat_service.py#L198)，198–204 行，以及 205 行之后的助手消息落库。

`finally` 中对 iterator.aclose/client.aclose 的异常没有独立处理。该异常在前面的生成异常处理之外，`safe_stream` 只捕获 AppError、ValueError、KeyError；若关闭时发生连接/传输错误，会直接跳出生成器。此时即便已经向访客发送 delta，后面的助手消息保存和 done/error 均不会发生，客户端得到无终止事件的断流，重新拉历史也没有已看到的助手内容。

**合成复现：** 运行真实 `safe_stream` 和真实 ChatEngine，用合成测试会话及明确注入的客户端 `aclose()` → ConnectionError；使用身份问题使 engine 正常先输出策略回答，再触发清理。

- delta：**1** 个。
- done：**0** 个；error：**0** 个。
- 逃逸异常：**ConnectionError**。
- 助手消息持久化调用结果：**0** 条（内存数据库记录）。

这是故障注入证明的异常路径，不是宣称当前供应商每次都会在 close 时抛错；与同会话并发 lease 问题无关。

**最小修复方向：** 清理两个资源各自保证尝试执行，记录清理错误但保留原有取消/生成异常；保证已发内容的落库与可识别终止策略不会被清理错误跳过。不要通过重新生成/重放内容修复。

**回归：** 分别注入 iterator.aclose 和 client.aclose 失败，验证另一项清理仍尝试、已发内容可恢复、连接未取消时收到可识别终止；取消场景继续保留取消语义。

## 验证记录与交接

复现脚本及白名单证据仅在项目未跟踪目录 `.local/agents/gpt-review/`：

- `verify.py`：隔离合成验证，无用户 .env、无真实数据库、无外部模型。
- `evidence.json`：上述状态码、布尔判据与事件数量；不保存令牌或密码。
- `sources.json`：受影响源码 hash 及与 4fbdf82 内容一致性。

本轮验证命令使用 server 现有 `.venv/Scripts/python.exe` 执行该脚本，退出 0；HTTP、真实知识存储与故障注入共覆盖上述四种场景。没有运行全量 `scripts/check.sh`、没有声称真实 MySQL验证通过、没有扩大到完整应用验收。

优先处理 P1 的 revision 批准绑定，再由对应所有者补鉴权与异常路径回归。此报告仅给出发现与建议，不修改任何业务、依赖、根配置、已有验收测试或主线程任务状态。
