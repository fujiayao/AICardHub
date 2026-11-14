# opus-h5 首批 candidate 交付说明

- 工作区：D:/AIWork/智能名片/worktrees/opus-h5；分支 feat/opus-h5-redesign；基点 c02fb77。
- 首批提交：2e3744e0677d14d7d3a711a001358af447d21c60。17文件，498新增/82删除。代码由官方 Claude Code 指定 Opus 实现；最终 git 提交由 Codex 调度者执行，未将调度者冒充 Opus。
- 内容：A1紧凑无照片身份头、姓名徽标、长企业名换行、AI浮卡、44px引导、无电话隐藏拨号；A2欢迎/气泡/留资视觉、安全Markdown、逐消息展开、公开来源标签；共享tokens和loading/error/empty；A4/A3样式整理。
- 设计依据：根/子AGENTS，docs/UI设计规范.md、H5原型.html，根早期原型仅参考。实际执行用户指定 ui-ux-pro-max 的 --design-system/--stack vue。舍弃搜索绿金和Google Fonts，采用原型深蓝/蓝/AI青绿、中文系统字体。
- 实际模型：消息model为 claude-2/claude-opus-5-5；两个native Agent启动回执resolvedModel同值。调用Read/Grep/Glob/Write/Edit/Bash/PowerShell/Agent等，精简证据见 opus-h5/execution-evidence.json。Agent启动不等于完整完成，未宣称其13页交付。
- 检查：lint通过（最初7项正则规则错误，Opus已修复）；vue-tsc --noEmit通过；Vite生产构建通过；现有15测试全部通过（CLI --testTimeout=30000，首次默认5s有2项子进程超时；未修改测试断言）。pnpm自动依赖检查受core-js构建策略阻断，使用已安装工具的node入口执行上述检查，无新增依赖。
- 截图：未完成。Magpie浏览器50s超时；本地Chrome启动/导航超时。已准备浏览器本地合成fixture脚本但没有成功截图，不能算真实业务验收。未重建demo/colleague账号，未读取.env/key/private knowledge。
- 预览：主线程5193，不启动/停止该服务。
- 明确未完成：员工B1-B13全套结构改版、业务/展会场景接入、完整18页对比、真实exec-01验收。backend CONTRACT-v2已由人确认，已读；活动/归属生成契约尚未交付本分支，未手改generated、未做假切换。
- 模型阻塞：后续candidate/staff两个Opus进程出现真实429 rate_limit（分别至少3/2次）；已停止这两个重试，不无限等待，不切GPT。需主线程协调限流恢复后继续。
- 无后端/数据库/接口schema改动；无迁移；主库未写入。

全局视觉brief：opus-h5/global-visual-brief.md，可由主线程转发adminworker。


## onceai 同模型续作（2026-11-14）

- 路由验证：只读 metadata 后，一次110秒有界Read probe成功；消息model=onceai/claude-opus-5-5，结果canonicalModel=claude-opus-5-5。每轮一个实施进程，未新增Agent，未改global，未用GPT。
- 员工候选提交：ab9e972（10文件基础员工页）、6a94a66（编辑/详情/场景预留）、b172edc（知识流程/tokens/真实组织契约生成）、31d6291（五个表单弹层/试聊及报告）。代码由onceai Opus实际Read/Edit/Write；前几轮有PowerShell回执，最后两轮仅原生读写，协调者执行检查与Git。
- B1-B13现已有页面或主要承载组件实际改版覆盖；此为代码候选覆盖，不是完整视觉验收。B10薄路由复用已改版CustomerList；B4场景仍pending，禁用预留不等于接通。五个表单组件实际改版为AssistantEditor/NoteEditor/CorrectionSheet/PasswordSheet/LeadStatusSheet；报告若写全部7个组件应以此精确列表为准。
- 最新检查：全局lint、vue-tsc通过；15测试全部通过（21:11:31，33.10s）；生产build通过（7.47s）；员工样式颜色字面量/300行扫描无问题。未宣称浏览器、主库、权限或活动联调通过。
- 组织契约：真实脚本读取后端66ae4a1 OpenAPI生成42operations，SHA f409ed1fbf23f3a57b819c0de8198880bb9d75129943d8429abc1650a3084722。Staff已新增归属/登录状态/可空电话；CardData仍无company_name，未强加字段。
- 后端最后检查至9bf4c05，campaign_paths仍为空；活动正式接线是本轮必做但当前仍未完成，等待schemaowner生成活动契约。不能用旧API或临时stub冒充。
- 视觉brief已实际投递adminworker本地调度目录H5-GLOBAL-VISUAL-BRIEF.md及H5-HANDOFF.txt，文件hash一致。
- 精简回执：opus-h5/onceai-execution-evidence.json。
