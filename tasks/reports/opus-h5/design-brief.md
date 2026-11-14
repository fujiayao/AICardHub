# opus-h5 设计简报（Design Brief）

## 设计方向
商务、克制、可信。瑞士式网格 + 留白，品牌深蓝为身份底色，主操作蓝只用于行动，AI 青色只标识 AI 分身。
ui-ux-pro-max `--design-system` 返回 "Enterprise Gateway / Minimalism & Swiss"：**采纳**其结构建议（清晰层级、44px 触控、可见焦点、reduced-motion、SVG 图标、无 emoji）；**拒绝**其配色（#1E3A5F/#16A34A 绿色 CTA）与 Google Fonts（Poppins/Open Sans）。`--stack vue` 查询无数据库命中（0 results），按通用规则执行。

## 调色板（全部来自 src/styles/tokens.css）
| 角色 | Token | 值 |
|---|---|---|
| 品牌深蓝（身份、标题、头部底色） | --c-ink / --c-ink-2 / --c-ink-3 | #13294B / #22406E / #3A5A8C |
| 主操作 | --c-primary / -press / -soft / -line | #2F6BFF … |
| AI 分身 | --c-ai / --c-ai-soft / --c-ai-line | #0E9E98 … |
| 提醒 / 危险 / 成功 | --c-amber / --c-danger / --c-success | 不变 |
| 中性 | --c-bg / --c-surface / --c-line / --c-text(-2/-3) | 不变 |
字体：系统中文字体栈 `--font`；数字 `--font-num`。不引入网络字体。

## 页面层级
- A1 名片：身份头部（有照片=全宽职业照；无照片=深蓝紧凑身份区：姓名首字徽章 + 姓名 + 职务/部门 + 公司，公司名可换行 2 行）→ 浮起 AI 卡（开场白 + 引导问题）→ 快捷操作（仅显示可用操作：无手机号不显示拨号）→ 联系方式 / 关于我 / 公司 / 主营业务（横向卡片）→ 底栏主 CTA「和TA聊聊」。
- A2 对话：分层 calm 背景（ai-soft → bg）；欢迎区（身份 + 开场白 + 引导问题）；气泡安全 Markdown（段落/列表/标题，无 v-html）；每条消息公开来源 chips；留资卡片。
- A3 留资成功 / A4 停用 / A5 微信引导：层级清晰，保留行为。
- B1–B13 员工端：登录、名片主页/编辑/分享、助手、客户、消息、我的。统一卡片、表单、空/错/载状态。B4 分享预留“商务/展会”场景选择 UI（禁用态 + pending 说明，不改分享 URL）。

## 组件归属
| 归属 | 文件 |
|---|---|
| 主控（我） | styles/tokens.css、styles/base.css、components/common/**、utils/kb-refs.ts、utils/markdown.ts |
| 访客 worker | components/visitor/**、pages/card/**、pages/chat/** |
| 员工 worker | components/staff/**、pages/staff/** |

## 不变量
无照片 + 无手机号是主状态。公司名 20 汉字需换行不溢出。kb_refs 只渲染公开安全标签，私有/未知路径用通用标签。不编造公司/高管/演示内容，不用 emoji、网络字体、虚构头像、logo 当人像。单文件 ≤300 行，tokens only，无 any。