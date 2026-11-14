# 浏览器验收计划与 runner 交付

日期：2026-11-14。开工 main：`cc4dce3`。仅交付 `e2e/browser/**` 与本文；未 commit，未修改 `e2e/local_acceptance.py` 或业务实现。共享主仓库的其他变更由其他执行者产生，不纳入本次交付。

已读根 AGENTS、工程框架 §10.2、冻结契约、UI 规范及原型 `docs/H5原型.html`、T42/T50。遵循 Vue 黑盒 E2E 的用户可见定位、自动等待、真实行为断言，以及 Python 测试指导中的隔离、清理、Arrange/Act/Assert 原则；本次不新增 Python 测试。

冻结契约 SHA256：`3BC264FF88CE00541EA4D2A778D53DFE5A7DC46E339816510030003D207CC832`。

## 已交付范围

- 独立 pnpm runner，精确锁定 `@playwright/test@1.65.1`，不加入根 workspace，不影响两个前端的独立依赖。附 `pnpm-lock.yaml` 及 pnpm 11 安装生成的局部 `pnpm-workspace.yaml`。
- 默认 H5 5173 / API 8000 / admin 5174；seed 凭据仅在内存读取 `server/local-credentials.json` 的 admin/employee/colleague，兼容 UTF-8 BOM。
- 390×844 运行访客、员工业务链路一次；后台 1440×1000 运行公司资料、新员工链路一次，链路中的移动端为 390×844。360/430×844 仅布局与主要页截图。
- 真实 UI 操作配合真实 API 数据核对；无路由替身、无模拟成功结果、无自动重试、无 skip/xfail。
- trace/video/自动失败截图关闭；禁用自动页面快照、丢弃 Playwright 原生失败产物，避免 error-context 复制动作错误；密码填入异常改为固定诊断。定制 reporter 仅输出用例名、状态、代码位置与错误计数；密码、typed 值、认证 headers、token、storageState、控制台原文和堆栈不入报告。截图屏蔽密码控件。
- console.error 和 pageerror 非零使业务/布局用例失败；console.warn 计数保留，不隐藏。覆盖主 context、显式访客/员工 context 和新页面。
- 精确视口截图与 full-page 长图分别输出，原型编号/状态/宽高/用例标识入文件名，每次运行独立目录；有溢出结果清单，不伪造截图或填满 18 页数量。

## 测试与原型/模板映射

H5 工程模板：`vue3-vant-mobile`；后台模板：`pure-admin-thin`。本 runner 不验收模板安装来源或实现质量，仅映射实际界面行为。后台 C 页不受 H5 的视觉 tokens 规范约束。

| 用例文件 / 流程 | 模板、原型 | 核心断言 | 当前状态 |
|---|---|---|---|
| runner.spec.mjs / 浏览器启动 | runner，无业务原型 | Chrome 真正启动、DOM、390 宽度 | 已实际通过 |
| runner.spec.mjs / 错误观察器 | runner，无业务原型 | 注入 error/warn/pageerror，计数正确且无文本持久化 | 已实际通过 |
| h5-visitor-lead.spec.mjs | H5 A1/A2/A3、B2/B10/B11/B13 | 引导问题→SSE 多 delta→done→可见答复；手机号只提示；未同意不建线索、提交禁用、默认未勾选；明确同意仅一个请求，持久化；30 秒内通知；已联系刷新后保留；同事 GET/PATCH 为404 | 已编写，未执行业务 |
| h5-card.spec.mjs | H5 B1/B2/B3→A1 | 员工登录、编辑个人简介、访客立即可见、UI 恢复、API 字段快照恢复验证 | 已编写，未执行业务 |
| admin.spec.mjs / 公司资料 | 后台 C1/C2/C3→H5 A1 | 管理员真实登录、公司简介保存刷新持久、访客可见、恢复并比对 | 已编写，未执行业务 |
| admin.spec.mjs / 新员工 | 后台 C1/C7→H5 B1/B2/A4 | UI 创建账号并生成名片、首次必须改密、新密码登录、助手存在；账号停用、公开卡不显示姓名 | 已编写，未执行业务 |
| layout.spec.mjs / 两个视口 | H5 A1/A2/B1/B2/B3/B4/B5/B6/B8/B9/B10/B12/B13 | 360/430只导航、标题或接口文本真实可见后截图、根滚动与元素越界检查、业务写请求必须为零 | 已编写，未执行业务 |

## 18 页状态覆盖账本

“已编写”仅表示有待联调脚本。当前没有执行任何产品页面，不存在可交付产品截图。

| 原型 | 已编写的采集点 | 待补/限制 |
|---|---|---|
| A1 | 390 默认、员工简介变更/恢复、公司简介变更；360/430 默认 | 职业照与标题首屏、长姓名6字/公司20字、安全区、资源≤300KB、产品横滑、复制/分享/vCard/导航专项 |
| A2 | 390 对话、未同意留资弹层；360/430 空状态 | 逐帧增量渲染而非仅 SSE 多事件、首字等待、断网/重试/限流、恢复历史、点踩/复制 |
| A3 | 390 明确同意后成功 | 360/430成功态、脱敏摘要、重复留资规则、继续聊/返回 |
| A4 | 新建验收员工停用后390 | 360/430停用态、全部个人字段与操作均不得泄漏 |
| A5 | 无 | 微信 UA 存通讯录引导/关闭/复制、真机微信 |
| B1 | 390登录/首次改密；360/430登录 | 密码规则/不匹配/锁定/过期/退出、首次改密路由守卫 |
| B2 | 390员工主页/新员工；360/430只读 | 统计与三处未读数字一致性、分享/访客视角 |
| B3 | 390简介编辑；360/430只读 | 头像上传裁剪、二维码上传/删除、字段锁定、未保存退出 |
| B4 | 360/430默认 | 390及二维码/海报/链接全部状态、来源参数、真实复制与长按 |
| B5 | 360/430默认 | 390、模板切换/润色/开场白/引导问题持久化 |
| B6 | 360/430列表 | 390、空/编辑/删除确认、公开批准边界 |
| B7 | 无 | PDF/DOCX解析预览→编辑→选中入库；草稿不自动发布 |
| B8 | 360/430列表 | 390、新增/删除/优先级、个人纠错不得擅自公开 |
| B9 | 360/430只打开 | 390、试聊→纠错→再问真实生效，测试会话不计客户/统计；与批准边界及 FakeLLM 夹具协调 |
| B10 | 390线索列表；360/430默认 | 访客态、筛选/分页/空态、意向等级、精确脱敏格式 |
| B11 | 390新线索/已联系 | 360/430详情、访客轨迹/会话/摘要/备注、通知已读 |
| B12 | 360/430默认 | 390、修改密码/帮助/退出 |
| B13 | 390真实线索通知；360/430默认 | 全部已读/分页/空态、铃铛/标题/Tab 数量一致 |

后台待补：C3 产品增删改；C4 模板与默认；C5 回答规则；C6 知识上传/编辑/历史/回滚/公开批准撤销；C9 问题池；C10 配置与密钥不可泄漏；后台角色拒绝、导航与审计专项。C8 NFC 独立物理管理按冻结裁决延期，不验收假按钮为完成。

UI §7 的 tokens、44×44点击区、按下态、所有空/加载/错误态、长文截断、iOS Safari/Android/微信真机截图与人工原型比对均未完成。桌面 Chrome 移动视口不等于真实设备兼容验收。

## 联调约定与数据清理

1. 前端 DOM 未合并：当前使用有语义的 label/role/name 作为测试契约，主线程核对文字、表单 label、dialog 名称、菜单和状态 radio。缺少语义时应修前端可访问性，不用 CSS 层级遮掩。员工入口按 UI 规范 `/staff/login`，与部分启动说明 `/login` 的差异待主线程核对。
2. 旧 UI A2 写“手机号自动建线索”，冻结契约明确要求只提示，采用后者；默认卡 code 用 `demo`，不用旧 T42 `sk0001`。未同意禁提交、多 delta、模型标识、持久化、404、恢复和溢出断言不降低。
3. 服务端必须实际运行 FakeLLM。测试对完整答复要求多个 delta 且 done.model 为“本地演示模型”；若 seed 引导问题没有合适的已批准公开合成知识而走 policy，应补夹具/明确知识边界，不能将模型断言删掉刷绿。现阶段未验证最终 seed 内容。
4. 名片与公司简介使用 UI 正常恢复，失败 finally 通过原字段 API 恢复且核验。需要隔离的本地演示库，执行期间不与其他人同时改这些资料。线索最后标记 invalid；每次完整运行新增一名员工并停用，不承诺无残留。聊天、通知、已读、审计和统计属于真实副作用。强杀进程可能跳过 finally，需人工复核。
5. 360/430只导航与截图，允许登录、访客初始化、访问计时、空聊天/试聊会话；不发送聊天、不提交线索、不修改公司或员工。发现其他写请求直接失败。所有主要页若尚未实现会失败，保留待联调状态，不 skip。
6. trace/video关闭，report不输出输入、请求体、认证头或浏览器错误原文。严禁为调试开启动作日志或改为通用 reporter 后对真实凭据运行。报告只给代码位置，现场可在不录制秘密的条件下复核失败。
7. `scripts/check.sh --e2e`/PowerShell 检查集成属于主线程；本次不得改 `scripts/**`，未接入，也未运行全仓 `check.sh`。主线程可在其检查入口调用 `e2e/browser` 的 `pnpm test` 并保留退出码。

## 实际验证证据

2026-11-14，本机 Windows、Node `v24.18.1`、pnpm `11.25.0`：

| 操作 | 实际结果 |
|---|---|
| `pnpm install --ignore-scripts` | 成功，仅安装3个 Playwright 包；浏览器下载0套 |
| `pnpm install --frozen-lockfile --ignore-scripts` | 成功，锁文件可复用 |
| `pnpm check` | 所有 runner `.mjs` 语法检查通过 |
| `pnpm test:list` | 成功收集9项：2 runner、1 readiness、2 H5业务、2后台业务、2布局 |
| `pnpm test:runner` | 2项通过，真实启动已有 Chrome；DOM断言、密码输入异常脱敏及错误观察器通过 |
| `pnpm preflight` | 非零退出：缺少主仓库 `server/local-credentials.json`；未打印文件内容 |
| 产品业务/布局执行 | 未运行；不等待尚在开发的 router/前端页，不宣称通过 |
| 产品截图/18页审图/G3 | 未执行，没有伪造截图；未签字 G3 |

最初自检发现 globalSetup 把只运行 runner 的情况也误当业务预检，已改为仅业务项目依赖 readiness.setup 后验证通过。该修复未降低业务前置条件。

启动步骤与配置见 `e2e/browser/README.md`。交付判断：runner 准备已验证，业务用例已编写待主线程合并后联调；T42/T50完整验收与 G3 均未完成。

## 有界静态对齐：交主线程转 Maxwell

2026-11-14，读取 `D:/AIWork/智能名片/worktrees/h5/apps/h5/src` 的在建文件。未运行 H5、未修改业务。当前工具未发现 Maxwell 的直接消息入口，因此通过本清单与最终回复交主线程转交。源码仍在写，本清单是一次观察快照，不将暂缺文件认定为最终交付缺陷。

| 项 | 实际源码证据（相对 H5 src） | 测试影响/处理 |
|---|---|---|
| 客户列表路由 | `components/staff/StaffShell.vue:7` 的 Tab 是 `/staff/customers`；`pages/staff/card/index.vue:15` 的“查看全部”为 `/staff/customers?tab=visitors` | runner `/staff/customers` 与现有导航一致。暂不改为 `/staff/visitors` 或 `/staff/leads`，API 资源名不等于页面路由 |
| 客户详情 ID 类型 | `pages/staff/card/index.vue:15` 的最近访客跳转 `/staff/customers/${visitor.id}?kind=visitor` | runner 留资链路要打开 Lead，不可把 visitor.id 和 lead.id 混用。请 Maxwell 在客户页、通知导航明确区分 `kind=visitor` 与线索类型；runner当前不猜 lead 查询参数，待实现后对齐 |
| 消息路由 | `components/staff/StaffShell.vue:7` 消息按钮 aria-label 为“消息通知”，跳转 `/staff/messages` | runner路径一致；不要按 `/staff/notifications` 推断。API仍是 `/me/notifications` |
| 页面尚缺 | 首次读取 `src/pages/staff` 只有 login/me/card/index/edit/share；收尾文件枚举时 assistant/index、notes、import 已新增。两次枚举均未出现 customers/messages 文件；`pages/[...path].vue:2` 是“页面不存在或链接已失效”兜底 | B10/B11/B13与状态弹窗当前不能静态确认；本轮未追踪持续新增的助手页面。360/430巡检会对缺页失败，不会误将兜底页截图当产品截图 |
| 状态弹窗 | `utils/format.ts:4` 已定义 new/contacted/converted/invalid 及“新线索/已联系/已转化/无效”，当前没有消费它的状态弹窗实现 | 待 Maxwell 确认“标记状态”按钮、可命名 dialog、`radio 已联系`、确定/保存及真实 PATCH `/me/leads/{lead.id}`。runner保留UI选择、PATCH结果、刷新后状态和API持久化断言，不虚构实际DOM |
| 名片首页 | `StaffShell.vue:7` 使用真实 h1；`pages/staff/card/index.vue:15` 的编辑名片为 van-button，Vant当前依赖默认渲染 button | runner `heading 我的名片`、`button 编辑名片`相符；首次登录页、A3/A4的heading也相符 |
| 统一页标题缺 heading 语义 | `components/common/PageShell.vue:7` 使用 van-nav-bar title；本地 Vant `es/nav-bar/NavBar.mjs:86` 渲染普通 div | layout 对 B3/B4 的 heading 断言目前不匹配。建议 Maxwell 给统一页标题真实 heading（或 role=heading+aria-level），保持可访问导航。未用模糊文本替代删掉页面标题语义断言 |
| B3两个保存按钮 | `pages/staff/card/edit.vue:22` 顶栏 button“保存”+表单 native-type=submit“保存” | 已在 runner 对 B3 选唯一 `button[type=submit]` 与角色/名称交集，不用 first/nth；仍核对真实保存响应与恢复 |
| 留资输入标签 | `components/visitor/LeadSheet.vue:17` 手机为“联系电话”，checkbox的aria-label为“隐私同意”（覆盖可见长文案） | 已把runner匹配改为包含这两个真实语义名称，保留默认不勾、未勾禁提交、明确 consent=true、仅一次请求及落库断言 |
| 留资dialog名称 | `LeadSheet.vue:17` 的van-popup由当前Vant生成 role=dialog，但没有 aria-label/labelledby；内部有h2“留下联系方式” | runner改用 `dialog` 内含该heading来定位，不依赖不存在的名称；建议 Maxwell 给dialog关联标题以改善可访问名称 |
| 留资入口重复 | `pages/chat/[code].vue:47` 每个lead_prompt有按钮，另有常驻同名“留下联系方式” | 已把runner定位限定为本轮SSE lead_prompt.title 对应的语义section，避免同名按钮严格匹配失败；未用first随意点击 |
| 首次改密 | `pages/staff/login.vue:11,22` 在原路由切换“设置新密码”，原密码/新密码/确认密码、确认并进入；`stores/auth.ts:17`调用真实changePassword | runner正则与标签相符，保留真实首次标志与新密码重新登录。服务端 token 变更若要求重新登录需真实联调确认 |
| 聊天与隐私 | `ChatComposer.vue:8` aria-label为消息/发送；`ChatConversation.vue:13` log“对话记录”；`LeadSheet.vue:9,12,13` consent默认false、未勾返回、提交true | 与核心测试方向一致。SSE网络多delta不等于已证明逐帧增量渲染，后者仍待补 |

交 Maxwell 的待确认项集中为：B10/B11使用的客户路由及kind区分、B13通知跳转目标、状态弹窗的可访问语义、统一PageShell标题语义。其余已确认的真实标签和重复按钮由runner静态对齐。没有要求修改接口或放宽业务断言；没有启动未合并的服务。

静态对齐后再次验证：`pnpm check` 通过，`pnpm test:list` 收集9项，`pnpm test:runner` 2项通过。没有执行产品用例。到此结束本次有界检查，等待主线程另行安排服务合并后的执行。

## 后台真实执行与失败转诊（2026-11-14 16:58–17:05）

本节为后续实际执行，更新上文“尚未执行业务”的历史状态。用户授权仅测真实后台5174/API8000，H5先未启动、后因 `/card` 路由代理问题由主线程要求暂停。本轮没有访问H5，也没有重启业务。

为避免现有完整admin集成用例强行访问H5，新增独立 `admin-only.config.mjs` 与 `admin-only.spec.mjs`。`pnpm test:admin` 只运行后台公司资料/员工两条；完整C→A/B原用例保留为 `pnpm test:admin-integrated`，没有删除其H5展示、首次改密断言。本轮不声称完成这些H5断言。后台前置检查不依赖5173或FakeLLM声明，因为不发聊天请求。

已按真实DOM对齐管理员手机号/密码、登录管理后台、企业与产品、职务、保存员工等label/name。`loginApi` 原先误把seed账号附带的 `card_code` 一并提交，严格后端返回422；已修为只发送phone/password。首轮 `admin-first-20261114-01` 两项在此处失败，未进业务写入。原因已由安全诊断确认：账号对象字段名为phone/password/card_code；完整对象422，明确登录字段200。没有输出字段值或token。

修正后只再执行一次 `admin-aligned-20261114-02`，`retries=0`，worker=1。预检通过，两条业务用例均为failed，原因如下：

| 项目 | 具体结果与定位 | 归属/下一步 |
|---|---|---|
| 后台静态资源缺失（已复现） | 两用例各console_errors=1、page_errors=0；后续无写入浏览器诊断捕获console来源 `/favicon.ico:0`，直接GET确认404。浏览器图标请求可能不出现在普通page响应监听中，但console源和独立HTTP检查一致 | 后台owner修复favicon资源/HTML引用；不忽略console.error刷绿 |
| C1→C2→C3公司资料 | 四个命名步骤均passed：管理员UI登录/工作台；简介UI保存与刷新持久化；公开名片API同步；UI恢复与API完整对象比对。最终仅因fixtures.mjs错误守卫console_errors=1失败。rootWidth=viewportWidth=1440，截图采集点越界列表均为空 | 业务步骤通过，但整用例failed；修favicon后由主线程安排再验，不在本轮循环重跑 |
| C1→C7员工创建 | 管理员登录并打开新增员工表单passed；`tests/admin-only.spec.mjs:66`，`dialog.getByLabel(labels.phone).fill(contact.phone)`超时。此前只填了姓名，尚未点保存员工，没有POST /admin/employees。另有同一favicon console.error | 当前归类runner定位/页面更新时序待确认，不能报“创建员工接口失败”；不改业务、不降低断言 |
| 员工输入只读诊断 | 在同一真实后台按原顺序登录→员工页→新增→先填姓名→getByLabel手机号，匹配1个，3秒内填入成功；不提交、不保存 | 原超时未稳定复现；后续可在该步骤记录安全的匹配数/可见/可编辑状态，不保存typed值。当前不第三次跑业务 |
| 清理核验 | 公司API当前intro不含测试marker；查询q=浏览器验收返回total=0。公司原值已在用例中完成UI恢复并深比对，员工未创建，无账号清理动作 | 不存在本轮新增的测试账号或未恢复简介 |

没有证据将任何失败归因为后端重启。API health和管理员显式字段登录的诊断均200。主线程后来通知连接池已修、50并发通过，属于主线程证据，本runner未执行并发测试。

实际证据位于 `e2e/browser/artifacts/admin-aligned-20261114-02/`（ignored，不commit）：

- `results.jsonl`：前置通过、两项failed；`steps.jsonl`：公司4步骤passed、员工新增输入步骤failed。
- `runtime.jsonl`：两项各1 console_error、0 pageerror、0 warning。
- `evidence.jsonl`：C1/C2/C3真实视口与布局结果。
- `screenshots/admin/C2-admin-only-dashboard-1440x1000-c891025eb4.png`。
- `screenshots/admin/C3-admin-only-company-edited-1440x1000-c891025eb4.png` 与 `C3-admin-only-company-restored-1440x1000-c891025eb4.png`；均另有-full长图。

当前safe reporter新增仅输出固定test.step名与经过白名单匹配的源码文件:行号:列号，不输出error原文。运行时诊断追加控制台来源pathname/行号与失败资源status，丢弃query/headers/body/错误原文。后续失败可保存密码遮罩的视口截图，避免Vite错误页完全无证据；本轮原始admin失败时尚未启用此手工失败截图，因此不声称已有员工失败画面。原有trace/video/自动快照关闭与原生失败产物丢弃仍保留。

交主线程转后台owner：**确认 `/favicon.ico` 404修复**；员工新增表单手机号超时尚未复现，附原行号与只读复现结果供核对，不认定为已确认业务缺陷。未找到后台owner直接消息入口，由主线程转交。H5按最新指示暂停，不耗时等待，不运行390或360/430。

## H5 390真实执行、政策分支修正与当前阻断（17:10–17:15）

主线程确认5173真实可用、8000稳定后，串行执行 `h5-390-first-20261114-01`：readiness通过；员工登录→改简介→访客可见→UI恢复与API原字段比对通过，console/pageerror/warning均0，采集点无横溢。访客流程首问成功，第二条纯手机号联系消息在 `support/visitor.mjs` 的多delta断言处失败。

**对前次结论的纠正**：将每轮都要求Fake多delta是runner分支划分错误，不是seed或服务夹具缺陷。纯手机号问未命中知识时，诚实policy兜底、lead_prompt和不自动建线索正是产品要求；不应为了该问走Fake而补知识。用户明确此分支规则后，保留引导问Fake多delta标准，单独为 `phone-no-knowledge` 断言：至少1个delta、done.model=policy、nokb=true、kb_refs为空、诚实说明缺乏公开批准资料并引导人工确认、恰好一个reason=phone提示，以及无自动创建线索。

仅重跑访客用例一次，运行标识 `h5-390-branches-20261114-02`，未重跑已通过的改卡用例、未运行360/430、未重启服务。真实SSE安全摘要写 `streams.jsonl`（无消息原文/请求体/token）：

| 分支 | 实测delta/model/nokb/prompt | 结果 |
|---|---|---|
| guided-demo | delta=5、fake、nokb=false、prompt=0 | 通过，Fake多delta断言保留 |
| phone-no-knowledge | delta=1、policy、nokb=true、prompt=1 | 通过，诚实无知识与留资提示分支已直接证实 |

已实际通过至：A1首屏引导→A2真实聊天→手机号只提示（无自动POST/落库）→滚动到本轮prompt按钮→打开留资弹层→默认未勾同意、填表后按钮仍禁用→明确勾选→只产生一次同意提交→A3成功页→API新线索字段与session匹配→colleague GET/PATCH为404→员工登录→30秒内有对应站内信→B13对应通知可见。

**当前真实阻断**：`tests/h5-visitor-lead.spec.mjs:38`，点击对应站内信后仍在 `/staff/messages`，没有跳到客户详情，URL断言12秒超时。当前H5 `src/pages/staff/messages.vue:23` 的read(item)只POST已读并刷新未读数；没有router导航。界面还显示“当前消息接口未返回目标链接，点击消息可标为已读”。因此B13→B11、B10列表与标记已联系尚未执行，不能记为通过。UI规范跳转表要求B13点击消息进入相应详情，保留该断言，交主线程协调H5 owner及后端通知目标字段。不要通过直接goto客户页绕过通知跳转缺口。

本次浏览器console_errors=0、page_errors=0、warnings=0；所有已采集状态rootWidth=390且无越界元素。合成线索由finally PATCH invalid并GET核验成功，后续已联系步骤未执行。没有输出密码/token，没有把policy算作产品缺陷。

证据：`e2e/browser/artifacts/h5-390-branches-20261114-02/` 下streams/results/runtime/evidence清单，以及A1/A2聊天/手机号policy提示/未同意弹层/A3/B2/B13的390×844截图和长图。上一轮成功改卡证据在 `artifacts/h5-390-first-20261114-01/`。当前不继续重跑，等待通知跳转交付；360/430继续不执行。

## 360/430只读巡检与新增员工诊断补充（本轮后续）

主线程确认通知target schema缺失已交后端修复，授权等待期间先跑窄屏。未重跑通知链路，未重跑admin业务；执行 `AICARD_RUN_ID=layout-360-430-20261114-01 pnpm test:layout`，worker=1串行，无重试。readiness、layout-360、layout-430全部通过。

每个宽度采集13个真实视口状态：A1默认、A2空态、B1登录、B2/B3/B4/B5/B6/B8/B9/B10/B12/B13只读页。每张有精确360×844或430×844视口图及full长图，总计26个状态、52个PNG。已执行根scrollWidth及元素越界检查，不替代人工字体/tokens/截断/点击区审图，也不构成18页全部状态覆盖。未包含A3/A4/A5、B7、B11等状态。

两个宽度各console_errors=0、page_errors=0、warnings=0；请求守卫通过，未创建员工/线索或提交名片/公司/知识表单。允许登录、匿名初始化、访问计时、空聊天/试聊会话这些已明示副作用；不称数据库完全零写入。证据位于 `e2e/browser/artifacts/layout-360-430-20261114-01/` 的results/runtime/steps/evidence和screenshots子目录。

**后台新增员工“第二原因”精确定性**：原始错误为 `admin-only.spec.mjs:66` 对新增员工dialog内手机号的 `fill()` 12秒超时，不是点击保存后的422/500；没有POST /admin/employees，合成账号查询为0。原始safe reporter未保存动作原文，因此无法事后证明是标签尚未关联、控件重建还是短暂不可编辑。后续同顺序只读复现已确认：先填姓名后“手机号”匹配1，填入成功；尚无稳定复现证据。唯一已确认产品缺陷仍为当时favicon404（主线程已告知修复），不能另编造员工业务根因。

为下一次获准复验，runner把新增员工手机号限定为真实 `textbox` + 精确名称“手机号”，并在fill前依次断言唯一、可见、可编辑；失败将留下具体阶段和密码遮罩截图，而非只知总超时。本轮未执行这条业务，不将定位改善记为员工创建通过。通知target修复与后台候选修复尚待主线程另行安排业务复验。
