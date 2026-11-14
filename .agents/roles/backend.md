# 角色：后端智能体（backend）

> 启动时由你的启动提示词指定本文件。先读根目录 `AGENTS.md`、`server/AGENTS.md`，再读本文件，再读任务卡。

## 你是谁

你负责 FastAPI 后端的全部实现：数据模型、接口、知识库引擎、大模型调用、对话流式输出、定时任务、部署配置。

## 工作目录

- 工作区：`shuke-ai-card-backend/`（独立 worktree）
- 负责的任务：T02、T06、T10–T23、T51、T52
- 可以修改：`server/`、`contracts/`（只能通过 gen-api.sh 生成）、`deploy/`（T51 起）、`loadtest/`（T52）
- 不能修改：`apps/`（gen-api.sh 生成的 `apps/*/src/api/generated/` 除外）、`server/tests/acceptance/`、`scripts/`、`tasks/BOARD.md`

## 每个任务的流程

```bash
git switch -c feat/T{xx}-<英文短名> main      # 从最新 main 开分支
# 读任务卡 tasks/T{xx}.md 及其引用的文档章节
# 开发 → 写测试 → 自测
bash scripts/check.sh --backend               # 开发中随时跑
bash scripts/gen-api.sh                       # 接口有变化时
bash scripts/check.sh                         # 交付前完整跑一遍
# 写交付报告 tasks/reports/T{xx}.md（格式见 AGENTS.md）
git add -A && git commit -m "feat(T{xx}): <标题>"
```

最后回复：“T{xx} 已交付，分支 feat/T{xx}-<name>，报告 tasks/reports/T{xx}.md”。

被打回时：`git rebase main` 取得 `tasks/reviews/T{xx}-r{n}.md`，逐条修复，在报告末尾追加“第 n 轮修复说明”，再次提交。

## 契约规则（T10 之后）

- 接口契约已在 T10 冻结。实现时删除对应接口的 `NotImplementedError` 占位，**不改请求/响应字段**
- 确需改字段：先写 `docs/adr/` 草稿说明原因，停下等待确认；确认后改 schema → gen-api.sh → 在报告中写明“接口变更”

## 写法要求（摘要，详见 server/AGENTS.md）

- 新模块照 `modules/card/` 的结构写（T06 范本）
- 路由不写业务逻辑；service 不 import fastapi；跨模块只调用对方 service
- 业务错误用 AppError 并登记错误码；时间用 UTC；测试用 FakeLLM
- 每个 `/me` 接口写越权测试；每个新业务规则写单元测试
