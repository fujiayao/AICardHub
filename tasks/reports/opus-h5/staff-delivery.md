# 员工端（B1–B13）视觉改版交付说明

模型：onceai/claude-opus-5-5（本会话，无回退）。分支 feat/opus-h5-redesign。
写集：apps/h5/src/pages/staff/**、apps/h5/src/components/staff/**、本报告。
未触碰：访客/共享/common/styles/generated、后台、server、provider/env/私有知识、preview 5193。

## 实际提交
- `ab9e972` feat(h5): unify Opus employee business interface（首批 10 文件）
- 其余改动（B3 edit、B11 detail、B4 场景选择器、B6/B7/B8、token 违规修复）由协调者提交（本会话 shell 不可用，未自提交）。

## 逐页覆盖矩阵（B1–B13）
| 编号 | 页面/组件 | 状态 | 改动要点 |
|---|---|---|---|
| B1 | pages/staff/login.vue | 完成 | 左对齐专业抬头（品牌徽章+标题+副标），表单面板化，密码规则改图标核对项；brand-mark 色改 token |
| B2 | pages/staff/card/index.vue + StaffCard + StatsPanel | 完成 | 深蓝紧凑身份卡（姓名/职务/部门 overflow-wrap 安全换行、无手机号不渲染拨号、chip/文字全 token），动作按钮分级+图标，指标卡格化，图表 token 化 |
| B3 | pages/staff/card/edit.vue | 完成 | 职业照卡：预览/虚线占位态（图标+文案），上传标签图标化并隐藏原生 input |
| B4 | pages/staff/card/share.vue | 完成 | 手机卡媒体容器、按钮 block+图标；新增**诚实禁用**「商务/展会」场景选择器（标「待接口支持」，默认商务，disabled，不做假切换） |
| B5 | pages/staff/assistant/index.vue | 完成 | AI 青色 header（方形 AI 头像+标题，全 token），面板/状态沿用 |
| B6 | pages/staff/assistant/notes.vue | 完成 | 列表卡：标题+公开/私密彩色状态徽章、摘要、字数/修订 meta，右滑删除统一 |
| B7 | pages/staff/assistant/import.vue | 完成 | 虚线上传区（图标+标题+限制说明），文件行图标化，草稿卡头部（选择+删除）分组 |
| B8 | pages/staff/assistant/corrections.vue | 完成 | 来源彩色标签（试聊/客户对话/手动），问/答徽标两列对照，原错误回答折叠 |
| B9 | pages/staff/assistant/test.vue | 完成 | AI 欢迎层（青色方头像+标题+调试说明），开场白置于 AI 青色面板，引导问题改为「猜你想问」图标 chip 列表 |
| B10 | pages/staff/customers/index.vue + CustomerList | 完成 | 行卡重构：彩色状态徽章（new/contacted/converted）、公司名安全换行、需求 2 行截断、超时图标提示、访客行 chevron；筛选按钮 token 化 |
| B11 | pages/staff/customers/[id].vue | 完成 | 身份聚簇（姓名+彩色状态+电话层级），需求/备注分区，访客轨迹导航行；新增 scoped 样式 |
| B12 | pages/staff/me.vue | 完成 | 头像身份聚簇，设置按「账号/帮助」分组，单元格图标，退出按钮下移 |
| B13 | pages/staff/messages.vue | 完成 | 未读左边框+红点强调，时间戳带图标，分组日期弱化，正文次级色 |

## 表单/浮层组件
| 组件 | 状态 | 说明 |
|---|---|---|
| CustomerList | 完成 | 见 B10 |
| StaffCard / StatsPanel / StaffShell | 完成 | 见 B2；StaffShell 粘性抬头+分隔线 |
| AssistantEditor | 完成 | 头部标题+字数计，inset 文本域，润色/保存并排操作行，润色候选浮层头部化 |
| NoteEditor | 完成 | 标题 inset 分组，正文带标注 toolbar（chip 按钮）与 inset 文本域，保存/取消操作区 |
| CorrectionSheet | 完成 | 图标头部，问题/正确答案 inset 分组，原回答折叠，操作行 |
| PasswordSheet | 完成 | 锁图标头部，原密码/新密码两组 inset 分区，占位+帮助文案，操作行 |
| LeadStatusSheet | 完成 | 旗标头部，状态单选 inset 组 + 备注独立字段组，操作行 |

说明：全部 7 个浮层/编辑器组件本轮完成字段分组（inset）、区块标题（含克制图标）、文本域间距与统一取消/保存操作行；业务 handler/emits/校验/批准/密码逻辑未改。

## 约束遵守
- 严格 token：颜色仅 `--c-*`、间距 `--sp-*`、圆角 `--r-*`；已清除初稿的 `--sp5`、`#fff`、`rgba(255,255,255,…)`（StaffCard chip→`--c-on-ink-line`、各处白→`--c-surface`）。全仓 `color:#|background:#|rgba(|var(--spN)` 扫描：无匹配。
- 无新依赖、无 any、无 @ts-ignore、无 cast；所有文件 <300 行；`<script setup lang="ts">` 保持。
- 业务 handler / route / label / 权限 / API 调用全部未改；无手机号不渲染拨号；长单位名安全换行；无假手机/假公司/假人像。

## 契约状态（CONTRACT-v2 / 场景集成）
- 协调者已由后端组织 OpenAPI（commit 66ae4a1）生成 H5 客户端（实际 SHA f409ed1…，42 operations），非手改生成文件。
- 现状：`Staff` 已含 `company_id`/`company_name`/`login_enabled`、`Staff.phone` 可空；但 **`CardData` 仍无 `company_name`**，campaign 路径仍为空。
- 因此 StaffCard 不渲染单位名（CardData 无该字段，正确省略，待卡片契约补字段后再加）。
- B4 场景选择器为**诚实禁用预留**（pending，非 done）：campaign OpenAPI 尚未生成，不做假切换。待 `me_campaign_list` + s/e 上下文落地后由协调者接线（short_url/二维码/海报共用同一 s/e）。本会话不请求也不手改生成文件。

## 校验
- 上一轮本机实跑：vue-tsc --noEmit staff 文件无错误；eslint staff 目录 ESLINT_EXIT=0。本轮为纯样式/标记改动，未改脚本逻辑。
- 最终 lint/type/build/15 测试由协调者全局执行。

## 未完成 / 风险
- B1–B13 页面与全部 7 个 staff 浮层/编辑器均已完成结构性视觉改版；B4 展会场景集成仍为 pending（等待 campaign OpenAPI），非已完成。
- StaffCard 单位名待 CardData 契约补 `company_name` 后再加。
- 390×844 截图未在本会话生成（preview 5193 属 owner，未启停），留待协调者截图比对。
- 本会话 shell 不可用，未自行 git/commit 与运行校验；改动留待协调者提交与全局 lint/type/build/测试。
