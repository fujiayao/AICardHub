# NFC-00 / NFC-03 / NFC-06 安卓交付说明

状态：`software_done` + `awaiting_hardware`，不是 accepted。唯一安卓 owner：gptpro/gpt-6.1-sol；共享工作区 `D:/AIWork/智能名片/worktrees/nfc-implementation` / `feat/nfc-implementation`；不自行 commit。

- 基线：`d9014ad0cbe0b61a4f872ed6271f38765d864a9c`。
- 启动 OpenAPI SHA-256：`3EBE39CD03645B7C69558307F9E60097C4C2F9CCC98A327105CB630CDC64D4E2`。只消费现有公开 PublicCard/PublicCampaign；没有修改 API、生成文件、数据库或其他 owner 文件。
- 修改范围：新增 `apps/nfc-android/` 及本报告。包名 `cn.aicardhub.nfc`，versionName `0.1.0-candidate` / versionCode 1。构建版本、使用说明和完整边界见该目录 README。
- 合成工具闭环：2026-11-15 创建 `.agent-marker`，内容 `NFC-ANDROID-gptpro-gpt-6.1-sol-2026-11-15`，用工具读回完全一致；marker 已 gitignore，不作为产品文件。

已完成公开链接/App Link 严格校验、后台联网预览和重新核对、系统控件手动确认；五模式互斥；只读 Type 4 NDEF URI APDU；冷启动/前台/亮屏/解锁/单调时钟超时防护；活动截止；NFC/HCE 独立检测；NDEF 读取、容量/只读检查、显示已有内容、明确覆盖确认、写前再次核对内容、写后实时回读字节和 URI；无永久锁卡、无格式化未知标签；普通分享 `s=link` / NFC `s=nfc`，无 token、visit 或私有资料。

## 实际检查结果

2026-11-15 22:57（Asia/Shanghai），采用批准站点构建参数 `-PpublicBaseUrl=https://haiwex.com/aicardhub`，修复旧读取链接残留并同步协议 reset 后最终复查：

```text
testDebugUnitTest assembleDebug lintDebug
BUILD SUCCESSFUL in 22s
51 actionable tasks: 15 executed, 36 up-to-date
```

- JVM 测试 21/21，通过，0 failure / error / skipped：TrustedLinks 7，ModeController 6，Type4Tag 6，StickerPolicy 2。
- 测试覆盖根/子路径、来源与活动参数、重复/未知/双重编码/外域/凭据/遍历拒绝、重定向约束、5 分钟和活动期限、冷启动/后台/锁屏撤销、互斥与过期写入 token、固定会话、CC/NDEF/分段/非法 APDU/EOF/长 URI、实际容量和字节/URI 回读不一致。
- Android lint：0 error、5 warning。DataExtractionRules 1（无持久化名片或凭据、allowBackup=false，后续发布可显式增加 Android12+ 提取规则）、MissingApplicationIcon 1（系统控件候选无定稿图标）、SetTextI18n 3（本项目简体中文原生功能骨架，未作多语言资源化）。未禁用/压制规则。
- `apksigner verify --print-certs` 成功。debug 测试证书 SHA-256：`3a52fb1d1cb71b2b957b191fe6d232592bc98a03910711714dbb21b76ef43303`。没有创建或提交正式签名私钥。
- 最终候选 APK：`apps/nfc-android/app/build/outputs/apk/debug/app-debug.apk`，SHA-256 `11547DF93E8746D77A1BC888D9ACF06F1E54B02582670879EC8D6E12D5722304`。已冻结，不再修改源码或构建产物，交总控打包。
- `adb devices` 为空：无安装、截图、射频、真实标签写入或跨设备结果。原生软件候选不宣传已支持任何具体机型。
- 根 `scripts/check.sh` 不由安卓范围替代；由总控集成后运行，本报告没有把未运行的全仓检查标为通过。

## 构建环境处置证据

JDK 21.0.12 已存在，本轮未安装或改写全局 JDK。Android SDK/Gradle/缓存均在 `D:/AIWork/智能名片/.local/nfc-toolchain`。下载官方 Android commandline tools，完整读取 Android SDK 2019-01-16 条款后按已授权必要开发用途安装 platforms35 rev2/build-tools35.0.0/platform-tools，不批量接受不需要的许可。Gradle 官方下载跳转 GitHub 连接失败，腾讯镜像内容经官方 SHA-256 校验一致。wrapper 保持官方下载 URL 与固定校验值。

初次原中文路径构建受 AGP 非 ASCII 路径检查阻止，项目 `android.overridePathCheck=true` 后 Kotlin/APK 编译成功；测试 worker 因 JDK native GBK 与 UTF-8 参数文件的中文 classpath 错配报 GradleWorkerMain ClassNotFoundException，未执行断言。总控批准临时 `subst N: D:/AIWork/智能名片` 后使用同一真实文件的 ASCII 路径，21 测试、APK、lint 全部完成。结束停止本任务 Gradle daemon 并只撤销本任务 N: 映射；没有复制/迁移源码、修改系统编码或全局配置。

## 发布与硬件门槛

参考仓库提交/Apache-2.0 许可证已冻结并在 Android README 记录，但没有复制参考代码或依赖该库。生产分发需专用签名和域名根 assetlinks 合并/路径回归；debug 指纹仅用于候选核对。App Link 未在真实设备验证。

安卓→安卓/iPhone Type 4 接收、`6282` EOF 具体读卡器兼容、完整读取回调的 RF 证据、NFC 开关/锁屏/退出/冷启/钱包冲突、贴纸非 NDEF/只读/容量/提前移开/回读及金属材质、每组合 20 次矩阵均 `awaiting_hardware`。实体 NFC 调用不能保证在用户退出瞬间撤回已开始的写入；任何写中失败均要求重读，不能声称原内容保持。
