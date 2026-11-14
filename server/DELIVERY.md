# 本地后端候选交付记录

基线 `3fca087196f0a19a31d39ecc66c353e60c20d178`，分支 `feat/local-backend`。
冻结文本契约 SHA256 `238989ff74e5c075bab000a9a5bbd53e3872c837fc3ff047e4fc1f7333461f25`。
AI交付源 `092ae251` 已 cherry-pick 为 `44b6c7f`，未修改该代理拥有文件。

## 可集成内容

- FastAPI应用、JWT员工/访客用途隔离、首次改密、停用及重置token失效、管理员自身保护。
- 完整冻结契约路由、MySQL真实持久化、名片/企业/产品/模板/员工/助手/线索/通知/统计/问题/审计/设置。
- KnowledgeStore与ChatEngine真实接入；员工知识每次修改撤销批准；管理员可查看全部范围；访客仅检索公开批准版本。
- SSE独立数据库会话、线程池调用同步知识/图片/文档操作、MySQL原子限流。
- 初始Alembic迁移 `e70a56b63c35_initial_schema.py`，uv.lock，ruff与严格mypy配置，OpenAPI生成器。
- 幂等演示种子：admin/employee/colleague角色，demo/colleague名片；随机口令仅在忽略的local-credentials.json。
- /health 与 /api/v1/health 暴露llm_mode；PublicCard补齐wechat_qr_url，停用隐藏个人字段。

## 已运行验证

- MySQL8.0.46执行 `uv run alembic upgrade head` 成功；`alembic heads` 仅 `e70a56b63c35`。
- `uv run python -m app.seed` 成功，真实MySQL；未输出口令。
- `uv run mypy --no-incremental app`：31源文件成功。
- `uv run ruff check app alembic`：通过；格式化完成。
- `uv run pytest tests/unit -q`：74 passed，35.70s（AI与知识引擎）。
- 本执行者HTTP冒烟：health/login/session/SSE done成功。
- 总控独立HTTP/MySQL黑盒：12/12，5.23s（由总控报告）。
- 首轮总控50并发：0/50，35个500、15个IncompleteRead，33–35秒。日志确认QueuePool size5 overflow10 timeout30，路由依赖会话在流期未释放，生成器再申请连接造成池自锁。
- 修复：DB依赖 `Depends(get_db, scope='function')` 在响应发送前关闭路由会话；生成器仍自行SessionLocal。未增加连接池。
- 修复后本执行者同链路50/50，4.56s；总控独立重跑50/50，6.85s，p95 6.52s。主干报告 `tasks/reports/local-load-chat.json`（由总控维护）。

## 启动

在server目录使用uv：`uv sync --locked`、`uv run alembic upgrade head`、`uv run python -m app.seed`、`uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`。
当前后端工作区API监听8000，PID34800（候选提交时）；请避免重复起同端口。
OpenAPI：`uv run python -m app.export_openapi ../contracts/openapi.json`。

## 仍需后续完成/限制

这是本地候选，不是原一期全量完成或部署批准。
- 独立scheduler与摘要/日汇总/清理任务尚未实现。
- 员工Excel导入、后台知识批量上传/真实模型评测尚未交付；NFC独立物理管理按批准裁决延期。
- 文档导入提取真实文本并返回草稿，尚未通过LLM整理拆篇。
- 模板预览变量替换、企业/模板修改后重新渲染profile/persona文件尚需补全。
- 当前ID采用MySQL INTEGER（原建议BIGINT），已落库迁移不擅改，部署前需明确转换迁移。
- 分享每次GET新生成图片，尚无缓存；海报二维码尚复用qr来源；vCard尚未含头像缩略图。
- 并发同一会话锁在首事务提交后释放，后续仍需完整会话串行策略及取消落库专项测试。
- 当前卡/全局限额是消息计数，尚非Token预算；设置动态生效范围需加强。
- 各业务接口完整测试矩阵、jobs与真实模型/真机/灰度/正式部署均未宣称通过。
- scripts/check.sh在此基线不存在，未运行整个仓库检查；两个前端由独立执行者检查。
