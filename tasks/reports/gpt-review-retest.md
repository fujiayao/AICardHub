# GPT 独立审查四项修复复测

2026-11-14，Asia/Shanghai。结论：**四项原始合成复现场景全部 PASS，本轮没有复现出四项问题的残留。** 此结论限于下述独立合成验证，不替代真实 MySQL、浏览器、完整流取消矩阵或主线程全量 pytest。

## 版本与执行方式

- 复测提交：`214a432e1c20cbd7b81a6cefaabbd20551004e23`。
- 核对关联修复：backend 扩展 `ad8f83c`、密码规则 `3f264f3`、知识回滚 `c94997b`；H5 在 `214a432` 集成改密后重新登录。
- 复用上一轮 `.local/agents/gpt-review/verify.py`，只在进程内调整测试适配，没有改写该 harness、原证据或业务文件。本轮唯一新增的持久交付文件是本报告。
- 使用 server 现有 Python 虚拟环境，合成验证总上限 60 秒；实际总耗时 **13.953 秒**，退出 **0**。执行输出时间为约 **17:49:08 UTC+08:00**。
- `service.py`、`kb/store.py`、`chat_service.py`、`knowledge_service.py`、`schemas.py` 的本次读取内容均与该提交一致，比较时归一化 CRLF/LF。

环境仍为 `Settings(_env_file=None)`、合成签名材料、未使用的假数据库端点；未读取 `.env`、用户凭据、演示账号口令或真实知识。HTTP 通过真实 FastAPI 应用与 httpx ASGITransport 执行，知识使用真实临时 KnowledgeStore/Git 修订和检索，数据库为明确的 MemorySession 替身，没有连接主线程服务或真实 MySQL，也没有外部模型调用。

## 复测结果

| 原问题 | 实际复测结果 | 判定 |
|---|---|---|
| 自行改密后旧 token 仍有效 | 原 token 的 profile 请求先为 200；改密 200；原 token 再请求为 **401**；token_version **0→1**；新密码登录 **200**；新 token 访问 profile **200** | **PASS** |
| 未批准草稿回滚后继承公开批准 | 创建私有未批准 r1 为 200；发布另一正文 r2 为 200；回滚 r1 为 200，生成 r3；恢复草稿正文，但 **public=false、approved=false**；真实 search **不返回该正文** | **PASS** |
| 损坏 PDF 返回内部错误 | 同一损坏 PDF multipart 输入，现在返回 **422 / VALIDATION_ERROR** | **PASS** |
| 上游关闭异常跳过落库与终止事件 | 注入 primary.aclose 的 ConnectionError 后：**1 delta、1 error、0 done**，无逃逸异常，新增 **1 条助手消息**；primary 与 fallback 各关闭尝试 **1 次** | **PASS** |

### 改密用例的必要调整

新密码 fixture 已调整为 **17 个 ASCII 字符，包含字母和数字**，满足新规则 8–20 字符；不再使用上一轮较长的密码。旧密码也采用合成 fixture，报告不输出密码或令牌值。

改密后旧 token 失效是本次期望行为，不把它误判为后续知识/上传验证的鉴权失败。harness 通过真实登录路由用新密码取得新 token，再执行后续 HTTP 请求；未绕过鉴权依赖直接注入管理员身份。

### 流生命周期用例的必要适配

新版 chat 从 `runtime_settings.clients` 取得主备客户端，因此故障注入迁移到该正式工厂：primary 关闭时抛合成 ConnectionError，fallback 正常关闭。复测仍经过真实 `safe_stream`、`stream` 和 ChatEngine。

新版引入 render 上下文和数据库 lease。为保持本轮只复测原清理异常，render 提供空合成知识/人设，数据库执行返回合成成功行数；没有验证 MySQL 原子 lease 的正确性或性能。使用身份问题使真实策略引擎正常输出，之后触发关闭异常；这不宣称已覆盖真实上游内容流、网络断开或所有取消时序。

观察到的 warning 仅含客户端类型与 ConnectionError 类型，流没有把合成异常正文作为业务错误返回。助手消息计数来自内存替身的 add/commit 路径，本轮不把它等同于真实 MySQL 持久化落盘。

## 证据摘要

```json
{
  "old_token_after_password_change": {
    "before_status": 200,
    "change_status": 200,
    "old_token_after_status": 401,
    "token_version_after": 1,
    "new_password_length": 17,
    "new_login_status": 200,
    "new_token_profile_status": 200
  },
  "rollback_unapproved_revision": {
    "create_status": 200,
    "publish_status": 200,
    "rollback_status": 200,
    "returned_revision": 3,
    "public": false,
    "approved": false,
    "unapproved_marker_restored": true,
    "public_search_returns_unapproved_content": false
  },
  "invalid_pdf": {
    "status": 422,
    "response_code": "VALIDATION_ERROR"
  },
  "client_close_failure_after_delta": {
    "delta_frames": 1,
    "done_frames": 0,
    "error_frames": 1,
    "escaped_exception": null,
    "primary_close_attempts": 1,
    "fallback_close_attempts": 1,
    "assistant_messages_persisted": 1
  }
}
```

## 通过边界与交接

本轮对原四项问题没有剩余失败需要反馈。没有重复研究或扩大为新功能审查，没有改业务、根配置、现有验收测试或主线程任务状态。

以下属于未覆盖的验证边界，不是本轮新增失败：

- 数据库真实事务、版本持久化、lease 释放及并发：留给主线程真实 MySQL/pytest 扩展。
- 上传：本次复用原损坏 PDF 用例，没有重新运行 DOCX/合法文档全矩阵。
- 流：本次覆盖 client.aclose 失败及备用客户端继续清理，没有执行 iterator.aclose 失败、重复取消、实际网络断开全矩阵。
- H5 改密跳转和浏览器 token 清理：本次只验证服务端接口，不冒充浏览器通过。

用户告知实际 API 12 项测试已通过、主线程 pytest 扩展进行中；本报告不重复执行、不将该告知计为本轮实测结果，也不提前宣称全量测试通过。原始审查与此次复测应一并保留：[独立审查](gpt-independent-review.md)。
