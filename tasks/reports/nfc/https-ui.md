# HTTPS NFC 前端交付

日期：2026-11-16。执行：当前 Codex 原生子代理，未使用 Magpie 或外部模型 CLI。工作区 `D:/AIWork/智能名片/worktrees/nfc-implementation`，基线 `bbe9ea0`。独占 apps/h5、apps/admin 本次 NFC 页面及必要工具、测试；未改后端、安卓或部署配置；未自行提交。

## 实现

- 保留现有组件职责：NfcSharePanel加载本人公开链接与用户操作，NfcInstallHelp展示真实下载；公开/share/nfc预览并提供独立唤起/复制；nfc-link纯函数处理受限URI；platform是唯一运行环境判断入口。
- Android用户点击采用标准 intent URI，scheme=https、固定package=cn.aicardhub.nfc；browser_fallback_url为编码后的同一受控HTTPS帮助地址。未安装时进入帮助页，已安装可显式选包唤起，避免同域链接停在浏览器。没有自动开始RF、自动写入或传递登录令牌。
- 公开帮助页加入“已安装，打开 NFC 助手”和“复制 NFC 名片链接”，安装后无需回到员工页循环；仅active名片开放操作。iPhone保留接收说明，微信要求外部浏览器，非安卓不提供假唤起操作。
- 去除NFC安装、后台Scope中的调试候选/未发布文案，换为安装与真实操作说明；Scope与菜单标题改“NFC 分享与贴纸”。实物库存/挂失等未实现功能继续明确，不伪报已完成。
- APK下载地址通过两端VITE_NFC_APK_URL注入，无硬编码域名。生产构建采用 https://haiwex.com/aicardhub/downloads/aicardhub-nfc.apk；总控负责将此文件实际发布。

## 实际检查

- H5 `pnpm lint`、`pnpm typecheck`：通过。
- H5 `pnpm test --run`：11 files / **51 passed**，新增3项intent/fallback/公开短链用例。
- H5生产build：通过，VITE_BASE=/aicardhub/；输出apps/h5/dist。
- Admin lint（eslint+prettier）、typecheck：通过；tests **27 passed**；生产build通过，VITE_BASE=/aicardhub/admin/；输出apps/admin/dist。
- 两端dist静态检索确认实际APK URL存在；H5现代/legacy产物含intent://；两端index入口前缀正确。
- UI机械检测4个修改SFC结果为空；git diff --check无错误。
- 构建警告保留现有H5 Vite configLoader/PostCSS提示及admin500KB chunk提示，没有压制规则。

## 冻结与边界

两端dist已向总控确认freeze，可上传，随后仅补本报告不再改产物。主线程进行服务器真实页面/接口检查及截图；本代理没有把JVM/browser模拟当作手机NFC结果。真实机型、App Links系统关联与RF读写由用户手机验收。

最终补充：后台菜单文字在第一次构建时命中旧模块；仅重新执行admin生产build（13.04s）后产物入口为/aicardhub/admin/assets/index-B18qiPV5.js。当前后台dist已重新冻结，旧菜单文字不再存在；主线程按新dist覆盖发布即可。

下载按钮修复：NfcInstallHelp将Vant Button显式tag="a"，增加使用真实Vant组件SSR渲染测试，确认实际<a href=APK>而非无效button。该测试与NFC工具测试共13passed，lint/typecheck再次通过，H5相同生产环境重build成功（5.75s）；index SHA256 16d04cecda38ed474e19ab445557d98046e364a1e9525d78e8f5d729946ec626。新dist已冻结。

最后仅文字修正：管理员登录页移除“本地候选”前缀；员工我的页about显示1.0.0。无逻辑改动，两端相同生产配置重build通过，H5入口/aicardhub/assets/index-KG295fMR.js，index SHA256 f0b4b63dadc93811b43cc21f9b92d627a58cc75ed8a1771cc9277cd58b067ea8；后台入口/aicardhub/admin/assets/index-Cim06srH.js，index SHA256 0d61157dc992d20a7b3908bbc2719df8e2e17bab6f4322af78bf55d7fee78883。产物再次冻结。
