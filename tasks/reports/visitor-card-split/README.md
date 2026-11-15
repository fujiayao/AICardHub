# 访客名片首页与AI对话页拆分

2026-11-15。负责人要求把原深色单页作为访客AI对话页，复制同视觉体系构建信息优先的名片首页；A1用于内容及交互参考，不重新换成浅色UI。

## 实现

- 源提交`c34caf5` → 主线`c93be4a`。
- `/card/:code`：共享原DarkCardHero与dark-card.css；直接展示真实联系方式/地址、个人简介、公司介绍（三行展开）、主营业务横滑卡，再展示AI入口。底部固定“和TA聊聊”。不挂载输入框/消息，不创建空会话。
- `/chat/:code`：沿用原深色Hero、DarkInlineChat及DarkMessages；增加返回名片按钮。字体、颜色、圆角和主要间距未变；没有切换回旧浅色聊天页。
- 五种来源`s`及活动`e`传递；引导题、产品题带`q`进入chat并只发送一次；旧`/card?q`、`/card?lead=1`兼容转入chat。停用名片先拦截，不泄露历史/个人信息。
- 原sessionStorage对话key不变；首页新访问、chat复用进行中/缓存访问，直接chat无缓存则创建；并发旧请求不能覆盖新访问缓存。首次发送才创建会话。
- 信息缺失不编造：当前高管未公开手机/邮箱时隐藏对应操作，地址及已公开资料可直接查看。无个人简介则整块隐藏。

前端由Claude Code经Magpie量惟`claude-2/claude-opus-5-5`完成，最后修正调用退出码0；协调器做审查和机械检查，主线独立验收。未改员工页、后端、OpenAPI或依赖。

## 验收证据

- H5 typecheck、lint、**24项测试**、production build通过。构建保留已有PostCSS警告。
- `navigation-style-verification.json`：qr/nfc/link/poster/sig五入口→名片→对话→返回；均未产生空会话；360/390/430宽度无横向溢出，无页面错误。
- `chat-style-baseline.json`与迁移后computed style比较：7个关键区域的背景/字体/圆角/间距 **零差异**。仅新增44px返回导航，不声称整页截图像素完全相同。
- `synthetic-state-verification.json`：字段齐全的合成HTTP样本；活动、个人/公司/产品、公司展开、q只发一次、刷新历史、产品复用会话、旧q/lead深链、明确同意与disabled全部通过。此测试没有修改生产数据库，也没有调用模型。
- `live-chat-verification.json`：独立`/chat`真实`gpt-6.1-terra`身份问答成功，刷新恢复历史。
- 另人工浏览器检查董事长名片归属数智集团且不混用词元产品；vCard下载成功；员工登录仍为浅色。

截图：`old-card-chat-390.png`旧基准；`home-390.png`新首页；`chat-390.png`迁移后对话；`chairman-home-390.png`董事长首页。A1原型原始SPEC提取于`A1-reference.json`。

## 本地入口

- 楼航宇名片：http://127.0.0.1:5173/card/5dbb1d43?s=link
- 楼航宇AI对话：http://127.0.0.1:5173/chat/5dbb1d43?s=link
- 董事长名片：http://127.0.0.1:5173/card/ffe358d1?s=link

仍使用用户启动的8002后端，未启停服务。没有推送或部署。未重新跑全后端（本轮纯前端）、未做实体NFC/微信真机验收；仅验证其网页入口及模拟浏览器状态。原有未完成员工端任务仍保留，不作为本轮完成范围。
