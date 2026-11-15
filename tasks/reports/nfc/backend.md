# NFC-01 后端交付证据

## 任务与执行环境

- 工作区：`D:/AIWork/智能名片/worktrees/nfc-implementation`。
- 分支：`feat/nfc-implementation`；基线：`d9014ad0cbe0b61a4f872ed6271f38765d864a9c`。
- 结果提交：由总控统一提交，本 agent 未自行 commit。
- 执行模型：本次派工标识为 Magpie 路由 `gptpro/gpt-6.1-sol`；这是总控传入的实际调度标识，当前执行会话无法独立读取供应商底层模型元数据。业务自动测试均强制 `LLM_MODE=fake`，清空三个模型密钥并禁用备用模型，不调用真实模型。
- 工具闭环：在本工作区 `tasks/reports/nfc/backend-marker` 写入 `nfc backend tool loop`、读回相同内容、随后仅删除本 agent 的 marker；执行工具返回退出码 0。
- 工具：`functions.exec_command`、`functions.apply_patch`；测试解释器复用主仓 `AICardHub/server/.venv/Scripts/python.exe`，所有源码导入、pytest 和导出均在本工作区 `server` 执行。环境只读取主仓 `.env`，未显示密钥。

## 完成内容

- 新增 `GET /api/v1/me/card/share-link`，`operation_id=me_card_share_link`、Staff Bearer 鉴权，使用当前员工 `staff.id` 获取本人的名片。
- 参数 `s` 为既有 `Source`（`nfc/qr/poster/link/sig`），默认 `link`；`e` 可选且为正整数。只允许这两个查询参数，额外 `employee_id/code/url/jwt` 返回 422。
- 响应严格为 `{short_url, source, campaign_id}`，无活动时 `campaign_id` 显式为 null。域名和部署前缀来自受控 `public_base_url`，编号经 URL 编码；长期 NFC 链接不带 `e`。
- 抽取不生成图片、不依赖字体或上传目录的分享链接 service；既有图片分享和新接口共用短链构造，二维码及海报分别保留 `s=qr`、`s=poster`。
- 复用公开活动有效期校验；草稿、结束、未开始、过期及不存在活动返回既有 404。已停用本人名片禁止生成新链接（409 `CARD_DISABLED`），停用账号沿用鉴权 401。
- `/c/{code}` 成功跳转增加 `Cache-Control: no-store`，保留根路径和 `/aicardhub` 部署前缀。未知名片 404；停用名片仍跳转访客停用页；请求中的任意外部跳转目标不进入 Location。
- 新接口不生成图片、不触发访问记录。未修改验收测试，无新增依赖，无数据库迁移。

## 修改文件

- `server/app/modules/workspace/schemas.py`
- `server/app/modules/workspace/router.py`
- `server/app/modules/workspace/media_service.py`
- `server/app/modules/workspace/share_link_service.py`（新增）
- `server/tests/unit/test_nfc_url_building.py`（新增）
- `server/tests/api/test_nfc_share_links.py`（新增）
- `contracts/openapi.json`（仅运行 `python -m app.export_openapi` 生成）
- `scripts/check-contract.py`（总控追加授权，登记新增必需接口）
- `tasks/reports/contract-check.json`（检查程序生成）
- `tasks/reports/nfc/backend.md`

## 契约

- OpenAPI SHA-256：`34240ff74f1a65f98a808c0c183bb1661fcfd2e1de3deda4d6b9f76f697570bd`。
- 契约检查：103 operations，issues=[]，passed=true。
- 前端生成文件由各端 owner 生成；本 agent 未运行会同时改写前端的全量 gen-api 脚本。

## 检查结果

- `ruff check app tests`：通过。
- `ruff format --check app tests`：71 files already formatted。
- `mypy app`：Success: no issues found in 44 source files。
- `pytest -q tests/unit`：385 passed in 222.21s。
- NFC URL、原分享生成、根路径、字体回归定向执行：51 passed in 7.82s。
- `alembic heads`：`a7c3e91d5b20 (head)`，单一迁移头。
- `scripts/check-contract.py`：通过，hash 如上。
- 真实 MySQL/HTTP API：隔离 MySQL 8（loopback 13316、专用 `aicardhub_test`），配置通过 `dotenv_values` 仅覆盖当前测试进程；新增 NFC API 22 passed in 48.69s。使用真实签发员工 JWT、当前工作区真实路由/service/查询，未 mock 被测业务对象。
- 全量 pytest：首次收集发现新建 unit/API 测试同名引发 pytest 模块名冲突；已将 unit 文件命名为 `test_nfc_url_building.py`，保留所有断言后重新执行。
- 全量实际结果：**532 passed, 2 failed in 287.27s**。两例均为既有 `tests/api/test_organization_migration.py::test_拒绝发生在任何DDL之前且保留当前结构[phone/password_hash]`，首次失败在隔离库缺少 `alembic_version`。本轮新建 NFC unit/API 用例全部通过。
- 经总控许可，仅对已核验 `127.0.0.1:13316/aicardhub_test` 的当前测试 schema 执行 `alembic stamp head`，再定向重跑上述两例：**2 failed in 2.38s**。此时版本表存在，失败推进至缺少预期命名外键 `fk_lead_campaign_id`。原因是测试 fixture 的 `Base.metadata.create_all` 建表不能替代真实 Alembic 迁移形成的结构命名；本轮无业务迁移改动，未修改该既有测试或放宽断言。
- 按同因连续失败规则停止调整测试基础设施并交总控/QA：建议重新建立空的隔离测试 schema，再以真实 `alembic upgrade head` 初始化后复跑这两例；勿用 stamp 冒充迁移验证。本 agent 未删除数据库或变更旧数据库。
- 全套前后端 `scripts/check.ps1`：由总控在前端完成后执行，避免并发生成文件。

## 未完成与边界

- 当前系统 MySQL80 服务停用；总控为本轮建立的隔离实例已支持通过上述 MySQL 用例，未修改旧实例与旧数据。
- 初次全量检查的两例隔离数据库结构前提失败完整保留在上节；总控后续在空实例以真实 `alembic upgrade head` 初始化后报告这两例已定向通过（总控执行证据，本 agent 未重复运行）。NFC 实现、真实 JWT/HTTP 22 例、单元 385 例、静态/类型/契约检查均已通过。
- 本交付不涉及生产发布、真实 NFC 射频、实体贴纸或手机兼容性验收；相关状态由 Android/QA/总控分别记录。

## 独立 QA P1 修复：浏览器失效活动恢复

- 状态：**completed**；未自行 commit，等待总控统一提交。
- 对合法名片 `/c/{code}` 的失效 `e`，只有 `Accept` 明确包含可接受的 `text/html` 才返回 404 HTML，清楚说明活动不存在、尚未开始或已经结束，并提供“打开普通名片”链接。
- 恢复链接为同站相对路径 `/{root_path}/card/{encoded_code}?s={source}`，移除 `e`、保留来源及部署前缀。名片必须先验证存在，未知 code 保持原 `CARD_NOT_FOUND` JSON 404，无恢复入口。
- 默认 Accept、`*/*`、`application/json`、`text/html;q=0` 和不可解析 q 值均保持原活动 `NOT_FOUND` JSON 404；有效活动及无活动短链仍正常 302。
- 活动判断与恢复模板在纯 service 内；router 只接收请求、调用 service 并构造响应。固定中文 HTML 模板，不回显请求目标，编号 URL 编码后再转义 HTML 属性；恢复页面含 `Cache-Control: no-store`、`Vary: Accept`、CSP、`nosniff`。
- 修改文件：`router.py`、`share_link_service.py`、`test_nfc_url_building.py`、`test_nfc_share_links.py` 和本报告。无迁移、无依赖变更、未修改 acceptance。
- 定向真实 MySQL 测试：`pytest -q tests/unit/test_nfc_url_building.py tests/unit/test_root_path.py tests/api/test_nfc_share_links.py`，**87 passed in 50.96s**。覆盖根路径与 `/aicardhub`、草稿/结束/过期/未开始/不存在活动、浏览器/API内容协商、未知卡禁止恢复、外域目标不回显、模板转义及原 NFC 接口回归。
- 全后端 `ruff check app tests`：通过；`ruff format --check app tests`：71 files already formatted；`mypy app`：44 source files 无问题；指定后端文件 `git diff --check` 通过。
- OpenAPI 重新生成结果与已有契约 JSON 语义完全一致，未改写生成文件；原始 SHA-256 仍为 `34240ff74f1a65f98a808c0c183bb1661fcfd2e1de3deda4d6b9f76f697570bd`。字节比较最初因已有文件换行形式不同报差异，随后以 JSON 结构逐字段验证无契约变化。
- 本轮按总控指令未并发重跑全套 pytest；全套检查由总控执行。
