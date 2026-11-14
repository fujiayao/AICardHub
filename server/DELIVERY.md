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

## 候选后测试补充

- `uv run pytest -q`：98 passed，37.01s；其中新增24项（19项schema/标记规则、5项真实MySQL测试）。
- MySQL测试仅允许DATABASE名aicardhub_test，不清空整库；覆盖线索/通知所有权、重复同意留资与不凭手机号归并、跨访客与调试会话隔离、调试不计统计、管理员自身保护/重置token版本、原子限流。
- 最终 `uv run mypy app`：31源文件通过；`ruff check app alembic`通过；`ruff format --check`自有应用文件和迁移通过。
- 生成契约64路径、85操作；`.env`与local-credentials.json均由git check-ignore确认忽略。
- 业务候选提交 `8713f4e`；本补充只增加自有测试和本记录，不改验收测试或AI代理文件。

## 扩展候选（2026-11-14）

本节取代上文中相应未完成项。新增独立APScheduler进程（python -m app.scheduler），会话结束摘要与A意向通知、超时线索待办、上海时区9点日汇总、调试7天/通知90天/匿名及对话180天清理。摘要单批10条，每条领取数据库租约、提交释放行锁后调用模型，再独立提交；JSON失败仅重试一次后C级，不伪造意向。

新增员工xlsx逐行导入（最多500行、大小和解压量限制、拒绝公式、密码不出现在结果/审计）、知识Markdown批量上传（仅未发布草稿）、模板/企业/名片变更资料重渲染；通过KnowledgeStore线程池写入，新内容撤批准。员工试聊仅本人卡私有资料的授权副本可见，访客仍仅批准公开资料。persona为system语气，人设不冒充事实来源。

固定运行设置白名单与严格类型校验，MySQL每次读取无进程缓存；主/备模型地址、模型、加密key、超时及三级消息限额立即作用于下次调用。密钥掩码或空串提交保留原值，clear_secret=true显式清空；真实模式下不允许清空导致配置不完整，应先切fake/停用备用。未知键拒绝，规则只走专用接口。GET /admin/runtime-settings返回安全掩码完整配置；health读取实际运行模式/模型，数据库或配置失败503，不输出地址/key。限额单位明确messages_per_day，尚非Token预算。

增量迁移cfe4fa4acaaa：card_access_grant转交授权及generation_token/expires_at租约。转交保留公开名片归属，接收人看关联访客会话，原员工不再拥有客户访问。生成租约=2*llm_timeout+30秒，最大270秒，原子条件含rounds<30。逐资源清理异常不阻断部分输出落库，取消最终传播。自主改密token_version++，旧token401需重新登录。损坏PDF/Word422。被清理访客token初始化401。

新增/me/card/wechat-qr独立重编码图片上传（5MB，仅更新二维码字段）。NotificationData增加target_type/target_id，LeadData增加visitor_id，VisitorDetail增加visits，会话增加intent_level/tags。新增employee_import/kb_admin_upload/runtime_settings_get/me_card_wechat_qr共4操作，OpenAPI现89操作。

验证：完整pytest121通过（296.44s，含新增23项），ruff check app tests、ruff format --check app tests全部通过，mypy38源文件通过；alembic heads单cfe4fa4acaaa、alembic check无差异。增量迁移已在开发库与测试库执行；测试库原由create_all生成，核对旧字段一致后stamp原revision再upgrade，未清空库。50HTTP全链路并发50/50、12.62秒；另有ASGI HTTP50流与延迟JSON摘要并行回归通过。API当前8000 PID3772；scheduler入口已测试注册，未启动常驻任务清理开发数据。

AI修复原样cherry-pick：5367d55/5960a90/f60d54f对应本分支0c912c8/98f0e94/b92faf4。主干已有无需重复取。未改AI内核与验收测试。

剩余限制：INTEGER/BIGINT、分享缓存/海报source/头像vCard、Token预算、文档LLM拆篇仍保持上文说明。数据库事务与版本化文件写入跨资源不原子：写入失败使业务事务失败；后续DB回滚时文件可能残留私有版本，但新生成内容均不公开且撤审批，须重新渲染/管理员复核补偿，不会自动批准。无正式模型评测/生产部署/真机/灰度通过声明。密码8–20规则补丁紧接单独提交。

## 密码规范补丁

依据docs/UI设计规范.md:353：修改、新建与重置密码8–20位，至少含英文字母和数字，允许符号。Login与old_password保留既有bcrypt72字节兼容。新seed随机口令为Aa9+token_hex(7)，17位；已存在seed账号与ignored凭据不改、不强制重置。密码专项8项通过（36.58s）；ruff与mypy通过。前端改密成功必须退登重新登录（旧token失效）。

## QA公司保存超时修复

真实开发库14员工，同值PUT公司信息耗时20.31秒，根因为同步render_all逐卡读取并Git写入。改为源数据事务中写Setting render_pending-{code}（不改已执行迁移），仅active员工与card。独立scheduler每30秒分批10条处理，按version条件清标记保留并发变更；API不启动scheduler。派生profile/persona在访客chat_context明确排除，后台禁止将这两类文件批准公开，即使旧文件曾公开也不进入访客上下文。知识正文原有显式批准规则保持。

回归：公司保存专项1通过（29.11s含真实Git后台渲染，保存本身断言<3秒）；资料重渲染/调度器/密码专项8通过（32.92s）。最终ruff app/tests、format app/tests及mypy38文件通过。上一轮全量165测试是在密码补丁生效前启动，其3个新增规则测试因旧进程加载旧schema失败（162通过），补丁后8项密码专项及本轮8项均通过；不将该旧进程全量运行声称最终全绿。主线程将在main统一全量回归。

## 原生Responses与三级运行配置补丁

产品专属地址/模型与真实密钥由主线程本地配置，本补丁不写真实供应商值、不调用真实模型。新增固定字段llm_api_mode、llm_fallback_api_mode、llm_tertiary_enabled/base_url/model/api_key/api_mode；协议仅chat_completions/responses。与AIowner 9ab2232（本分支75a9f43）原样接入；各级均经build_client，ChatEngine(primary,fallbacks=[...])严格主→备→兜底，最多两级后备，首内容后绝不重放。

三级共用llm_timeout；generation lease按启用级数*timeout+30秒，三级120秒配置为390秒（取代旧两级270秒），原子rounds<30保持。chat清理遍历iterator及所有客户端，每个关闭失败均继续尝试并安全记录类型、部分内容仍落库。jobs摘要使用同链路，首内容前才降级；总操作120秒、JSON最多两次尝试，取消传播，所有创建客户端逐个关闭。

兜底key加入固定secret白名单；与主备同Fernet加密/掩码/空串保留/clear_secret显式清空，env回退同样支持。未知键/未知协议/非严格类型/启用但配置不完整均拒绝。GET runtime-settings自动包含新字段且只返回key掩码。前端Erdos按llm_完整前缀接入，不新增泛化settings键；无API schema变更，导出OpenAPI无diff。

后台知识列表500修复：先排除profile/persona/rules派生文件再NoteData校验；管理员仍可审批私有notes/corrections，员工列表继续隐藏派生文件；外部NoteInput.content非空未放宽。

实际检查：新增协议/三级顺序/secret/env/摘要降级取消/空persona列表专项6 passed 45.09s（合成Fake+专用MySQL）；三级SSE实际落库、三客户端关闭、关闭异常、取消与租约回归4 passed 37.95s；摘要/调度回归4 passed 42.44s；AIowner test_llm 66 passed 2.16s。ruff app/tests通过、format46文件通过、mypy38源文件通过。未重新全量pytest；未启动API/scheduler，未运行seed，未读取或修改真实密钥。
