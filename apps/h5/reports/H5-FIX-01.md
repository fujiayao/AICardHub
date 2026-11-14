# H5 修复 01：生成入口、通知、二维码、改密与状态证据

基于已集成候选 31b8d98（main ce98bc1 同源）；仅 apps/h5，未推送。5173 保持运行，未编辑或停用 demo。

- 默认契约路径从包根 ../../.. 修为 ../..。真实后端契约临时放在本工作区 contracts/openapi.json 后执行无参数 pnpm generate:api 成功，临时共享文件已移除、未提交。新测试在临时 repo/apps/h5、repo/contracts 布局中从另一 cwd 运行生成器，验证默认路径不受 cwd 影响。
- 42 个操作从真实 OpenAPI 生成，SHA256 `9e95dce53b110e26a686585bd1a4b4abb9e4a3ecc0588e6100dd4373db248e1e`。新增 me_card_wechat_qr 与通知真实 target 字段。generated 均由脚本产出，供总控最终重生成。
- B13 已读后按 target_type/id 跳转；lead→默认线索详情，visitor→?kind=visitor，issue→助手。session/未知/无效 ID 不误映射为访客。移除旧“未返回目标链接”提示。
- B3 专用 multipart 微信二维码上传、5MB JPEG/PNG/WebP 校验、预览、失败重试、移除后保存。上传成功即时关联，文案明确；上传时禁用保存，避免旧 URL 覆盖。访客端仅有 URL 时显示加微信入口。
- 首次改密与个人设置改密在成功后均清 staff session/first-password 标记，跳登录并显示“密码已修改，请重新登录”。不续用旧 token。失败不清会话，visitor token 独立保留。
- A5 overlay 层级盖过固定底栏；截图关闭过渡动画，避免半透明过渡帧。
- 保持 /api、^/c/、/files 代理及原始 /files URL，不修改生产文件路径。

## 实际验证

- lint、typecheck、5 文件 13 单元测试通过。新增生成默认路径、通知 ID 类型、改密清会话/失败保会话测试。
- build 通过；仅原有 PostCSS from-option 与插件耗时警告。
- scripts/stage-browser.mjs 真实 Chrome 390×844，独立合成账号专项完成：首次改密→token清除→新密码登录；二维码 multipart上传→GET /files图片→URL持久化→访客展示；新线索通知→标已读→精确 lead ID 详情；设置改密→清会话→新密码登录；最终停用该合成卡→A4不显示姓名和聊天。0 pageerror。详见 stage-evidence.json。
- 专项不代表18页全部状态签字；没有更改独立 e2e 验收断言。
- A5 使用微信 UA 的桌面 Chrome 模拟，非真实微信设备；二维码素材为合成卡真实分享 QR，验证上传/读取，不声称实际微信扫码。
- 加载态延迟隔离浏览器的真实 API 请求；错误态仅隔离浏览器注入 internetdisconnected，点击重试后恢复真实 API。未伪造接口成功结果。
- B6/B10/B13 空态均来自独立新员工的真实空数据。最终专项账号已停用，留下合成数据/上传文件/访问/通知/审计作为可复核证据，没有删除主演示数据。

## 截图

reports/screenshots/stage 下 11 张 390×844：A1-loading、A1-network-error、A4-disabled、A5-wechat-guide、B6-empty、B10-empty、B13-empty、B3-qr-upload、A1-wechat-qr、B13-lead-notification、B11-from-notification。

下一批单独接最新 LeadData.visitor_id、VisitorDetail visits/intent/tags，当前已测提交不堆入该扩展。最终全仓 gen-api/后端权限会话撤销/e2e/360与430复验由主线程按最终契约统一运行。
