# HTTPS NFC Android release 交付

日期：2026-11-16。执行来源：当前 Codex 原生子代理，不调用 Magpie 或外部模型 CLI。基线 `bbe9ea0`；本 agent 未 commit，写入范围仅 apps/nfc-android 与本报告。

## 已完成

- 发布版本：`cn.aicardhub.nfc`，versionCode 2，versionName 1.0.0，应用名“数科 NFC 助手”；移除测试/调试候选标签，保留真实设备能力/错误说明。
- 本次部署 base：`https://haiwex.com/aicardhub`，Manifest 仅接管 `/aicardhub/share/nfc`，不接管 `/c/*`、`/card/*`。
- H5 显式 intent 唤起与正常 App Link 使用同一 HTTPS data；首次 Activity 启动将 URL 放入输入框，onResume 自动联网预览；onNewIntent 更新 URL、停止旧操作并重新预览。导入始终不自动开始 HCE 或写贴纸。
- 发布签名独立 RSA3072 PKCS12，存于主项目 `.local/nfc-signing/`，私有密码文件与 keystore 已限制 ACL 为当前 Windows 用户与 SYSTEM。没有将密码或私钥输出、提交 Git 或复制到服务器/公开目录。
- Gradle release 签名仅通过 NFC_SIGNING_STORE_FILE / NFC_SIGNING_STORE_PASSWORD / NFC_SIGNING_KEY_ALIAS / NFC_SIGNING_KEY_PASSWORD 环境变量注入；缺签名时阻止 preReleaseBuild。
- 增加应用 vector 图标与 Android12+ data extraction / 旧 backup exclude 规则；动态文本改字符串资源。

## 产物与公开校验值

- 源构建 APK：`apps/nfc-android/app/build/outputs/apk/release/app-release.apk`。
- 交接 APK：`.local/nfc-release/aicardhub-nfc.apk`，辅助元数据 `.local/nfc-release/android-release.json`。
- APK SHA-256：`6bdb83bf035366aa2117e48d16ec5ec440bd7d1ef7833888383d103f08aa998c`。
- 发布证书 SHA-256：`6D:5B:A4:2E:B8:FD:D4:BD:9F:7B:9E:9E:E5:E0:6C:F6:5A:92:59:DA:13:F2:97:95:93:08:EA:E9:96:18:1A:18`。
- apksigner verify --verbose --print-certs：Verifies，v2 true，单一RSA3072 signer。
- aapt badging：package/version/min26/target35 与上述一致，label“数科 NFC 助手”。

## 实际检查

使用既有项目隔离 JDK21 / SDK35 / AGP8.9.2 / Kotlin2.1.20 / Gradle8.11.1，临时空闲 N: 映射处理 Windows 中文参数路径。

`testReleaseUnitTest assembleRelease lintRelease -PpublicBaseUrl=https://haiwex.com/aicardhub`：BUILD SUCCESSFUL in 1m45s。

- 21 release JVM 测试，0 failure/error/skipped。
- lintRelease：No issues found，0 error / 0 warning。
- 构建日志仅本地 `.local/nfc-release-build.log`，不含签名密码。
- 构建结束已停止本任务 GRADLE_USER_HOME 下 daemon 并撤销本任务 N: 映射。

## 手机验收与升级

此 release 使用独立发布证书，与旧 debug 包不同。手机如装过 0.1.0-candidate debug，需要先卸载旧包，再安装此 release；后续升级保持发布证书即可。应用只持有公开链接的内存状态，无员工密码持久化。签名材料应由负责人离线保管备份，丢失将无法以同一签名升级。

真实 NFC 芯片、钱包路由、AlertDialog 确认期间移开/换标签、Android/iPhone 接收和贴纸写后回读未由本机执行；本次发布是可运行的实际实现供负责人手机验收，不以软件构建结果冒充射频验证。域名 assetlinks、下载地址和服务器发布由总控处理。
