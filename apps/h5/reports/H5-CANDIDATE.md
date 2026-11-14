# H5 本地候选交付（T03、T07、T30–T36）

- 工作区：worktrees/h5；分支 feat/local-h5；基线 3fca087196f0a19a31d39ecc66c353e60c20d178。
- 修改及提交仅 apps/h5；无数据库迁移、无共享契约改动、无推送。
- 官方模板先网络 clone 到临时目录，再复制 LICENSE 与工程配置改造；上游 SHA、版本及删减项见 TEMPLATE_SOURCE.md。
- Vue 3.5.45、Router 5.5.0 文件路由、Pinia 4.1、Vant 4.10.2、Vite 8.3.8、TS 6.0.3、UnoCSS 66.10.5、Vitest 5.1。实际版本以锁文件为准；独立依赖，无 workspace。
- 真实 OpenAPI SHA256：6e06c35ef71cd5cd99b25f7047942d3cea3197a7fe26c99938859040af1bfadc；从主仓库真实文件重新生成 41 个 H5 操作（后端全量 85 操作）。generated 未手改。临时开发契约不提交。

已实现 A1 名片、A2 SSE 聊天、A3 自愿留资成功、A4 停用、A5 微信通讯录引导；B1 登录/首次改密、B2 工作台、B3 编辑/3:4裁剪、B4 二维码/海报/链接、B5 助手模板/润色/引导问题、B6 私密笔记、B7 文档解析预览/逐篇保存、B8 纠错、B9 试聊、B10 分页客户、B11 线索/访客详情、B12 设置、B13 消息已读。

组件职责：共用页面状态/导航/聊天气泡/输入；访客头图/详情/留资/成功/停用；员工工作台/模板编辑/知识编辑/纠错/状态弹层。页面负责组合，异步读取、写入、分页、SSE、未读轮询放 composables；跨页面身份与未读计数放 Pinia。

- 每页加载/错误/空态或静态表单初态；API 失败显示重试，不编造企业内容和统计。
- disabled 只显示公司联络数据；visitor/staff Bearer 分开，过期访客清 token 后重新初始化；首次改密阻挡员工其他页。
- SSE 半包/CRLF/UTF-8/多事件/Abort；delta、lead_prompt、done、error；部分输出失败保留原文不自动重放。手机号聊天不会调用留资；显式勾选 consent 后才 POST。
- 本地演示标记读 health.llm_mode，亦可 VITE_LOCAL_DEMO=true。所有引导问题来自 API。
- 390 设计宽、最大 480 居中、tokens 与 Vant 主题映射、安全区；图标仅 lucide UnoCSS。
- 可访问 label/heading/dialog/radio 与按钮名称；/login 文件路由转 /staff/login。

## 实际检查

- pnpm install --frozen-lockfile --ignore-scripts：通过。core-js 的可选安装脚本不执行。
- pnpm typecheck：通过。
- pnpm lint：通过（最终提交前再次运行）。
- pnpm test 及 pnpm test --run：3 文件 8 测试通过。
- pnpm build：通过，cssCodeSplit=true，legacy 构建保留。上游 PostCSS from-option 和 Vite 插件耗时提示为警告。
- 手动重启 Vite；/card/demo、/chat/demo 实测 200 text/html，/api 与 /files 代理保留前缀。/c 以正则 ^/c/ 匹配，避免吞掉前端路由。
- 真实 Chrome 390 冒烟已完成 A1/A2/B2–B10/B12/B13 可达性及截图，最近结果 0 console.error、0 pageerror、0 console warning；截图等待真实内容，非骨架占位。
- 主仓库独立 Playwright h5-card：readiness + 员工登录→修改简介→访客立即可见→恢复原字段通过。没有修改验收测试。
- 全仓 scripts/check.sh 在此基线不存在；后端与 admin 不属此角色，不宣称全仓验收通过。

截图在 reports/screenshots/；A1-default-390x844.png、A2-chat-390x844.png、B2-workbench-390x844.png 等。A1 对比原型：保留440职业照区、底部身份、覆盖下沿AI浮卡、三问题、固定蓝色主按钮；合成 seed 没有真人授权照片，使用原区域头像占位。主线程已初审 A1 结构。

## 需后续联调与范围限制

1. 微信二维码公开展示已接新 schema；上传目前仍为已有图片 URL，等待 backend 提供专用上传接口后改为文件上传。
2. 职业照后端上传接口即时关联名片，UI明确说明即时保存；其他字段点击保存生效。原图10MB、裁剪后5MB。裁剪无需新增依赖。
3. 当前 NotificationData 不含 target_type/target_id，消息可标已读；代码已预留真实目标字段跳转，不能猜测 ID。需要后端公开字段后重生成并验收消息→线索。
4. 当前 LeadData 不含 visitor_id，线索页展示关联 session_id；访客记录从 ?kind=visitor 的独立入口读取，绝不混用ID。API未提供的访问轨迹/意向级别/助手未命中计数不编造。
5. 私密笔记/纠错公开批准规则以 API 为准；没有把保存草稿描述为访客立即可见。笔记简介放正文开头，当前契约没有独立简介字段。
6. NFC 实物管理按裁决延期，页面明确未开放。通知无系统推送，仅可见页30秒轮询。
7. 仍需独立完整留资链路、首次改密新账号、360/430、全部18页状态、真机微信/iOS/Android、二维码与海报来源参数、真实提供商模型验收。没有把本地 Fake 结果称为真实模型评测。
