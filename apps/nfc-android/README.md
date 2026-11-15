# 数科 NFC 安卓助手（软件候选）

`cn.aicardhub.nfc`，版本 `0.1.0-candidate` / versionCode `1`。本应用仅使用 Android 原生系统控件，保存于内存的公开名片链接，不含员工登录或令牌。未接真机，不在任何机型上宣称 NFC 射频验收通过。

## 冻结构建输入

| 输入 | 版本 |
| --- | --- |
| JDK | 本机 Oracle JDK 21.0.12（Java/Kotlin 字节码目标 17） |
| Android | min 26 / compile 35 / target 35；platform 35 revision 2 |
| Android Build Tools | 35.0.0 |
| Android Gradle Plugin | 8.9.2 |
| Kotlin / stdlib | 2.1.20 |
| Gradle | 8.11.1，仓库包含官方生成 wrapper |
| 测试 | JUnit 4.13.2（仅测试），Hamcrest Core 1.3（传递测试依赖） |

正式域名和部署前缀必须通过 `-PpublicBaseUrl` 或 `NFC_PUBLIC_BASE_URL` 指定；没有默认域名。构建参数必须为不含用户信息、端口、query、fragment 的 HTTPS 地址，例如本项目已批准站点 `https://haiwex.com/aicardhub`。Manifest 只关联 `{prefix}/share/nfc` 的完整路径，不接管 `/c/*`、`/card/*`。

常规构建（先设置自己的 JDK 和 Android SDK）：

```powershell
$env:JAVA_HOME = 'C:/Program Files/Java/jdk-21.0.12'
$env:ANDROID_HOME = '<project-local-toolchain>/android-sdk'
$env:GRADLE_USER_HOME = '<project-local-toolchain>/gradle-home'
./gradlew.bat testDebugUnitTest assembleDebug lintDebug -PpublicBaseUrl=https://haiwex.com/aicardhub
```

Windows 中文目录同时会触发 AGP 路径检查和 JDK native GBK/Gradle UTF-8 参数文件不一致。本次构建用临时 ASCII 盘符映射解决，实际文件仍在项目内：

```powershell
# 先检查 N: 未使用；只删除自己创建的映射。
subst.exe N: D:\AIWork\智能名片
$env:JAVA_HOME = 'C:/Program Files/Java/jdk-21.0.12'
$env:ANDROID_HOME = 'N:/.local/nfc-toolchain/android-sdk'
$env:GRADLE_USER_HOME = 'N:/.local/nfc-toolchain/gradle-home'
& 'N:/.local/nfc-toolchain/gradle-8.11.1/bin/gradle.bat' -p 'N:/worktrees/nfc-implementation/apps/nfc-android' testDebugUnitTest assembleDebug lintDebug -PpublicBaseUrl=https://haiwex.com/aicardhub
& 'N:/.local/nfc-toolchain/gradle-8.11.1/bin/gradle.bat' --stop
subst.exe N: /D
```

产物：`app/build/outputs/apk/debug/app-debug.apk`。该文件是 debug 测试签名候选，不能作为正式分发包。正式发布由发布负责人提供专用证书和域名根 assetlinks 关联，禁止把私钥放入 Git。单元测试报告在 `app/build/reports/tests/testDebugUnitTest/`，lint 报告在 `app/build/reports/lint-results-debug.html`。

wrapper 下载地址为 Gradle 官方 HTTPS 来源，固定 SHA-256 `f397b287023acdba1e9f6fc5ea72d22dd63669d59ed4a289a29b1a76eee151c6`。本机官方分发跳转 GitHub 无法直连，使用腾讯镜像下载，并与 `https://downloads.gradle.org/distributions/gradle-8.11.1-bin.zip.sha256` 官方值核对一致后解包。没有改写 wrapper 为非官方来源。

## 操作与边界

1. 从 H5 导入 `{base}/share/nfc?code=...&mode=emulate|write&e=...`，或手动粘贴 `{base}/c/{code}?s=nfc`。解析只解码一次，严格校验来源、前缀、code、参数；不接受 token、任意跳转地址、重复参数。write 拒绝活动 e。
2. 所有网络工作在后台线程。通过现有 `GET {base}/api/v1/public/cards/{code}?e=...` 核对 active 状态、公开姓名、公司和活动起止。最多两次同 origin、同 API 路径及参数的重定向，拒绝外域和其他路径。无网络不开始新模拟或写入。
3. 预览后用户主动确认，才进入模式。模拟需要 NFC 和 HCE；读取/写入只需要 NFC。所有模式互斥，每次最多 5 分钟；活动模拟以活动结束时间和 5 分钟较早者为限。离开前台、锁屏、息屏、停止、冷启动均关闭。每条 HCE APDU 都独立检查单调时钟期限与亮屏解锁。
4. 手机模拟提供只读 Type 4 NDEF URI，标准 AID `D2760000850101`；支持 CC、NDEF、NLEN、分段读取，最多 8192 NDEF 字节，超长拒绝且不截断。会话内容冻结，换卡使旧会话失效。仅完整覆盖读取后显示“链接已被读取”，不增加 visit，也不宣称网页打开。
5. 读贴纸仅显示内容；受信任公开名片可由用户显式选择打开。写贴纸先读取现有内容、可写状态和实际容量，再确认覆盖。比较 Android 编码后的 NDEF 字节数与 `Ndef.maxSize`；写入前再次读取防止确认期间内容变化；写后实时 `getNdefMessage()` 回读字节和 URI。未格式化/非 NDEF 不支持；没有格式化、锁卡、扇区或 UID 修改 API。
6. 操作失败回 idle。只读、容量不足、非 NDEF、移开、通信失败、回读不一致均有提示；一旦尝试写入，任何失败都提示内容可能变化、需要重读。系统 NFC 调用开始后的物理写入不能保证在页面退出瞬间撤回，退出后不显示成功，必须重读标签。
7. 普通系统分享构造 `s=link`；NFC 输出构造 `s=nfc`；助手不调用 visit 或对话接口。手机模拟/贴纸都受服务器停用控制，不能逐台/逐贴纸远程撤销已复制的公开链接。

## 许可证与参考

实现为本项目独立编写，未引入或复制参考库代码。方案参考仓库 `LuigiVampa92/ndef-emulator` 冻结提交 `eb67c76502c469347c7ce189aca6e4ea6eb654fc`，已核对 Apache-2.0 的 `LICENSE.md`，原文保留在 `docs/REFERENCE-LICENSE.txt`，SHA-256 `b728f1288180b9e33f1b15cd50508d5d5eed3039506f0a2fb866abdf252264ae`。

运行时依赖仅 Kotlin stdlib（Apache-2.0）。AGP、Kotlin Gradle Plugin、Gradle wrapper 为 Apache-2.0 构建依赖；JUnit 为 EPL-1.0、Hamcrest 为 BSD-3-Clause，均不打入 APK。Android SDK 受 Google Android SDK License Agreement 管理，不随源码分发。本轮已先完整读取 2019-01-16 SDK 条款，只接受 platform/build-tools/platform-tools 安装所需许可，未批量接受无关 TV/XR 许可。

## 尚需的验收

没有连接 Android/iPhone 或标签样品，`adb devices` 为空。Type 4 的跨设备 RF 路由、EOF `6282` 的具体读卡器兼容、钱包冲突、锁屏/后台行为和真实 NDEF 写入/回读仍须按 `tasks/nfc/贴纸写入与采购验收.md` 与设备矩阵验证。21 个 JVM 测试与 APK 构建成功不替代这些门槛。
