# T55 · 微信小程序壳

同一个小程序提供访客名片和员工入口。小程序不实现身份、对话、留资或拨号接口；名片/对话、员工登录与首次改密全部继续使用既有 H5。没有小程序登录、原生通讯录、电话页、订阅通知或摄像头权限；用微信自带的扫一扫打开小程序码。电话继续由 H5 使用 `tel:`，失败时复制或手动拨号。

## 导入和本地配置

1. 微信开发者工具中选择「小程序 → 导入项目」，目录选 `apps/miniprogram`，不选云开发，不构建 npm。仓库中的 `project.config.json` 使用 `touristappid`；无实际 AppID 时使用游客模式，仅验壳及未配置界面，不能证明业务域名、真机或发布可用。
2. 拿到获准的测试环境后，将 `config.local.example.json` 复制为 `config.local.json`，把 `h5BaseUrl` 设为实际 HTTPS H5 基址（形如 `https://example.invalid/aicardhub`，示例不可用）。支持站点根路径和子路径，末尾 `/` 可省略。不要填页面、端口、用户信息、查询参数或片段；基址子路径使用普通 ASCII 路径段。文件缺失、格式错误或非法基址均不打开网页。
3. 获准使用真实 AppID 时，在项目根目录的 `project.private.config.json` 写入 `{"appid":"<已授权的 AppID>"}`，重新打开项目并在「详情」核实生效；保留域名检查。两个本地文件都被 Git 忽略。H5 基址会进入小程序代码包，不能当秘密保存；不要在任何客户端配置中放 AppSecret、凭据或会话数据。见[微信项目配置文档](https://developers.weixin.qq.com/miniprogram/dev/devtools/projectconfig.html)。

## 路由和转发契约

| 小程序入口 | 行为 |
| --- | --- |
| `/pages/home/index` | 原生入口：访客使用微信扫一扫或好友转发，员工进入独立 H5 登录。 |
| `/pages/card/index?code=1a2b3c4d&s=poster&e=42` | 打开基址下 `/card/1a2b3c4d?s=poster&e=42`。名片内跳转 H5 对话不经过小程序路由。 |
| `/pages/card/index?scene=1a2b3c4d.42` | 小程序码入口，转为 `/card/1a2b3c4d?s=qr&e=42`。 |
| `/pages/staff/index` | 只加载基址下 `/staff/login`，忽略所有传入参数，不展示员工页转发。 |
| `/pages/share/index?code=1a2b3c4d&s=link&e=42` | H5 可用 `wx.miniProgram.navigateTo` 打开原生预览和「发送给朋友」。无活动时省略 `e`，不传标题、图片、URL 或会话信息。 |

- `code` 接受 ASCII `[A-Za-z0-9_:-]{1,32}`，区分大小写，不改写；冒号在生成路径时编码为 `%3A`。`s` 只认 `nfc`、`qr`、`poster`、`link`、`sig`，缺失或不合法默认为 `link`。`e` 是正安全整数（最大 `9007199254740991`），普通入口忽略非法 `e`。如果同时提供了 `code` 和 `scene`，使用普通入口校验，不混用参数。
- 原生转发始终重建 `/pages/card/index?code=…&s=link[&e=…]`。站内名片/聊天 `webViewUrl` 必须在配置的 HTTPS 基址内；只提取名片码和有效活动号。URL 不可用时用原入口；同一张名片的 URL 没有有效活动号时保留原活动号，不将活动号转给另一张名片。不会传递 `q`、`lead`、token、片段、员工路径或原网页 URL。分享封面是代码包里的通用图，不使用当前聊天屏幕截图。
- 右上角「··· → 发送给朋友」不依赖 H5 SDK 或 `postMessage`。H5 如使用官方 SDK 脚本，应确认实际 H5 HTML 响应的 CSP `script-src` 允许 `https://res.wx.qq.com`（官方脚本来源），不要放宽 `/files/` 或加通配符；业务域名配置和脚本 CSP 是两件事。

## 小程序码：精确格式

- [getUnlimitedQRCode](https://developers.weixin.qq.com/miniprogram/dev/server/API/qrcode-link/qr-code/api_getunlimitedqrcode.html) 由服务端或获准工具生成；`page` 必须是 `pages/card/index`（无前导 `/`、无查询参数）。本次不实现制码。
- 原始 `scene` 只可为 `code` 或 `code.e`，分隔符是一个字面半角句点 `.`。`code` 使用上述字符集（含 `:`，是微信允许的字符）；`e` 使用十进制数字。`scene` 整体最多 **32 个 ASCII 字符**，活动占 `1 + e` 的位数；例如 32 字符名片码只能用无活动的短格式。超长不截断、不丢活动，改用普通参数入口或由业务方另定方案。
- 生成时传原始值，例如 `1a2b3c4d.42` 或 `team:abcd.42`，不要传 URL 编码字符串；微信不允许原始 `scene` 含 `%`。开发者工具条件编译的查询参数则填 URL 编码后的 `scene`（如 `scene=team%3Aabcd.42`）。入口仅解码一次；非法、超长或带无效活动的场景整体拒绝。来源总是 `qr`。
- 条件编译仅验证参数。必须用目标 AppID 和目标版本生成**真实微信小程序码**，用 iOS 和安卓微信扫一扫实际打开并核对 `s`/`e`。普通 H5 链接二维码不验证此路径。体验版/开发版按官方 `env_version` 和 `check_path` 规则准备；正式发布另行审批。

## 验证和放行条件

从本目录运行 `node --test tests/*.test.js`，不安装依赖，不访问网络。AppID 注入、包内本地配置读取、WXML 编译和 `web-view` 平台行为仍须在开发者工具和真机验证：

- 游客导入看未配置页；获准测试基址下核对根/子路径、无效参数、无登录访客名片、名片到对话及流式回答。
- 两端测试 `web-view` 正常打开、微信自带加载提示、`binderror` 错误页、重试与返回。组件铺满页面，原生提示不是网页上的覆盖层；部分平台或 HTTP 错误可能显示微信/H5 自带错误页，不能以 Node 测试当作兼容性结论。
- 两端测试真实小程序码、从名片和聊天菜单转发（含禁用 SDK 的情况）、H5 打开原生转发预览、好友打开时只到名片，核对通用封面与来源/活动归因。核对员工页没有原生转发菜单，员工选取公开名片分享时也不转发员工页面。
- 实测员工登录/首次改密、登录态、退出、常用上传、访客 `tel:` 和手动兜底；记录 iOS/安卓版本、基础库版本和 390×844 对照截图。
- 上线前确认认证企业主体、正式 AppID、域名及 HTTPS/ICP，并在微信公众平台的小程序业务域名设置完成域名校验。仅发布名片时，壳应指向同时启用 H5 与后端开关的[纯名片部署](../../tasks/reports/T56.md)，而不是只隐藏小程序入口或指向仍开放模型的站点。若发布带 AI 的版本，按实际服务准备适用的备案/登记证明、授权及类目材料。最终以微信最新审核口径为准。

另见：[AI 提审材料和给服务商的询问模板](../../docs/微信小程序AI提审材料清单.md)。
