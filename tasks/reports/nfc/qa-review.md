# NFC 独立实现复核（第二轮）

日期：2026-11-15  
复核快照：`feat/nfc-implementation`，HEAD `d9014ad0cbe0b61a4f872ed6271f38765d864a9c`，工作区改动尚未提交  
OpenAPI：`34240ff74f1a65f98a808c0c183bb1661fcfd2e1de3deda4d6b9f76f697570bd`  
QA 边界：只读源码；未运行真实 MySQL、全量 pytest 或真机 NFC；仅新增本报告

## 结论

后端 share-link 的主路径、Android 的 URI/APDU/模式控制器/贴纸写入核心，以及 App Link 的受限 path 均未发现权限绕过、开放跳转或明显数据泄露。Android JVM 与构建证据可列为软件候选通过。

最终软件状态仍为 `changes_requested`：当前实现与冻结任务卡存在一处明确能力差异，活动失效短链没有文档要求的用户回退路径；发布工具的 base 校验也与 APK 构建校验不一致。若总控决定将临时活动贴纸和活动失效友好页移出本期，应先明确收窄契约，再由 QA 重评关闭这两项。

APK 真机状态仍为 `awaiting_hardware`，不能因 APK/JVM 测试通过而写 accepted。

## 阻断/需裁决问题

### P1：临时活动贴纸被全链路硬禁用，与任务卡 `mode=write&e` 约定不一致

触发：员工在展会活动下选择写入临时贴纸。冻结说明允许 `mode=write` 携带可选 `e`，并要求临时活动写入必须显式选择并提示到期后不能归因。

证据与行号：

- `tasks/nfc/角色任务卡.md:9`：`mode={emulate|write}&e={optional_id}`，要求长期 write 默认无 e，但临时活动写入须明确选择并提示失效行为。
- `apps/nfc-android/app/src/main/java/cn/aicardhub/nfc/core/TrustedLinks.kt:43`：任何 WRITE 带 campaign 都被无条件拒绝。
- `apps/nfc-android/app/src/test/java/cn/aicardhub/nfc/core/TrustedLinksTest.kt:21`：测试把 `mode=write&e=1` 固定为拒绝，已将差异固化。
- `apps/nfc-android/app/src/main/java/cn/aicardhub/nfc/MainActivity.kt:126`：Activity 再次拒绝带 campaign 的 write。
- `apps/h5/src/utils/nfc-link.ts:26`：write helper 始终丢弃 e；`apps/h5/src/components/staff/NfcSharePanel.vue:24` 也固定传 `undefined`。

影响：手机 HCE 模拟活动可用，但临时活动贴纸无法创建。长期贴纸安全路径没有回退。

建议：若该能力仍在范围内，保留唯一 `mode=write`，增加显式“临时活动贴纸”选择；仅该选择携带 `e`，在助手预览和最终确认处显示 `end_at` 及“活动结束后此贴纸仍打开普通名片或失效，且不能再归因”的提示。长期写入口继续固定无 e。补三组回归：`write` 无 e 成功、`write&e` 仅在临时选择成功、默认长期写入从不带 e。

### P1：过期活动短链直接返回 JSON 404，没有“打开普通名片”回退

触发：访客打开已写入活动 `e` 的 NFC 链接，活动已结束或未开始。请求在短链层终止，H5 名片页不会加载。

证据与行号：

- `docs/NFC手机名片接入与功能补充方案.md:148`：V1 要求可理解的错误页，以及移除 e、保留 s 的“打开普通名片”操作。
- `server/app/modules/workspace/share_link_service.py:54`：短链在返回前直接校验活动。
- `server/tests/api/test_nfc_share_links.py:195` 至 `:200`：当前测试明确期待 share-link、旧 share 和 `/c` 都返回 JSON `NOT_FOUND`，没有用户回退用例。
- `server/app/modules/workspace/router.py:101` 至 `:102`：只有有效活动才构造 302；错误时没有安全回退目标。

建议：让 `/c` 对活动失效进入可理解的 H5 状态，页面提供显式“打开普通名片”按钮并构造 `?s=nfc`（移除 e，保留 s）；不得自动静默归因。补根部署和 `/aicardhub/` 的 HTTP/浏览器回归。若本期确实取消该回退，应同步修改产品文档/任务卡，不能让现有测试成为与文档相反的唯一事实。

### P1：发布工具接受 APK 无法构建的 public base，可能生成错误 App Link 元数据

触发：发布者使用带端口、非法端口或 APK 构建器不允许的路径字符生成 release。

实际探针结果：`deploy/nfc/prepare_release.py` 的 `validated_base` 接受了

```text
https://example.test:443/aicardhub
https://example.test:bad/aicardhub
https://example.test/a.b
```

证据与行号：

- `deploy/nfc/prepare_release.py:13` 至 `:26`：只校验 scheme/host/query 等，没有解析 `.port`，路径字符限制也比 APK 宽。
- `apps/nfc-android/app/build.gradle.kts:8` 至 `:10`：APK 明确拒绝任何显式端口，路径仅允许 `/A-Za-z0-9_-` 段。
- `deploy/nfc/prepare_release.py:78`：随后用该宽校验结果生成 `app_link_path`。

影响：发布工具可能生成与 APK Manifest、assetlinks 或真实部署前缀不一致的发布材料；它不能识别 APK 实际构建域名。

建议：把 base 校验抽为与 APK 完全相同的允许集，访问 `.port` 并拒绝任何显式端口、非法端口、百分号、点号目录和非允许字符；增加上述三个负例。发布时最好从 APK Manifest/构建元数据读取并比对 public host/path，无法读取时至少要求人工提供同源构建配置并阻断不一致。

### P2：NFC base 没有单一运行时真源

触发：后端 `PUBLIC_BASE_URL` 配错，或 H5 通过别名 HTTPS 域名打开。

- `server/app/core/config.py:51` 的 `public_base_url` 没有 scheme/host/HTTPS 校验；默认值是本地 HTTP。
- `server/app/modules/workspace/share_link_service.py:25` 直接将其与 `/c/...` 拼接，生产误配可输出 HTTP、带 query 或非预期前缀。
- `apps/nfc-android/app/build.gradle.kts:8` 至 `:10` 对 APK 使用另一套严格校验。
- `apps/h5/src/components/staff/NfcSharePanel.vue:12`、`:23`、`:24` 用当前页面 origin 生成 App Link，而不是后端受控短链的 origin；员工端若从 CNAME/预览域打开，生成的链接不会被目标 APK 接管。

建议：生产配置启动时 fail closed，要求 `PUBLIC_BASE_URL` 为受控无凭据、无 query/fragment 的 HTTPS base，并校验 `AICARD_ROOT_PATH` 与其路径一致。H5 从后端返回的受控 URL 推导 App Link base，或与冻结 build-time public base 比对后再显示入口。补一项“别名 origin 不生成伪可用 App Link”的前端测试。

## 已核验的软件证据

- OpenAPI 实测含 `GET /api/v1/me/card/share-link`，operationId 为 `me_card_share_link`；`ShareLinkData` required 严格为 `short_url/source/campaign_id`，`additionalProperties=false`。
- 后端接口仅使用 Staff 当前 `staff.id`；无 employee/card/URL/JWT 请求参数；来源、活动、停用、前缀、无开放跳转和 `Cache-Control: no-store` 均有真实 MySQL/HTTP 测试。按总控提供结果记为 **22 passed**，QA 本轮未复跑 DB。
- `server/tests/acceptance/` 相对基线无变更；全量 `532 passed, 2 failed` 的两个既有 migration 前提问题属于总控测试环境处理，不作为 NFC 功能失败。
- Android 测试结果 XML 实读为 4 suites、21 tests、0 failure/error/skipped；lint 文件实读为 **0 errors, 5 warnings**（DataExtractionRules、MissingApplicationIcon、SetTextI18n ×3）。
- 当前 `app-debug.apk` 的 SHA-256 实读为 `11547DF93E8746D77A1BC888D9ACF06F1E54B02582670879EC8D6E12D5722304`，与 Android 报告一致；这只是 debug 测试签名候选。
- `deploy/nfc/test_prepare_release.py` 实际执行 **3 passed**；只证明当前合成元数据测试，不覆盖上述跨工具 base 不一致。
- `git diff --check` 无空白错误。

## Android 实现中已确认正确的关键点

- `TrustedLinks.kt:12` 至 `:18` 严格校验 HTTPS、origin、部署前缀；`:75` 至 `:89` 单次解码、重复/未知参数拒绝。
- `Type4Tag.kt:11` 至 `:51` 每个 APDU 取 live snapshot；AID/文件选择、CC/NLEN、分段、EOF、非法命令和切换失效有状态检查。
- `NdefUri.kt:6` 至 `:14` 使用标准 NFC Forum URI RTD，UTF-8 实际字节和长记录长度，超 8192 字节拒绝而不截断。
- `ModeController.kt:15` 至 `:39` 前台/亮屏依赖、模式互斥、单调时钟、5 分钟硬上限和 generation 撤销成立。
- `StickerIo.kt:31` 至 `:45` 写前重新读取、实际 `maxSize`、写后连接级 `ndefMessage` 回读、字节和 URI 双校验；失败提示内容可能已变化。
- `AndroidManifest.xml:19` 只关联 build placeholder 的 `/share/nfc` path；`apdu_service.xml:3` 要求设备解锁，AID 仅为 `D2760000850101`。
- H5 对外来源已分离：链接 `link`、二维码生成 `qr`、海报 `poster`、手机 NFC `nfc`；配置页不调用 visit。

## 非阻断风险与硬件边界

1. **Tag 跨用户确认持有风险。** `MainActivity.kt:181` 先检查并关闭 Ndef 连接，`MainActivity.kt:195` 至 `:208` 随后等待用户确认，再把同一 `Tag` 交给写入。若用户在确认期间移开、换贴纸或标签重新枚举，代码应 fail closed，但现有 JVM 测试没有 MainActivity/StickerIo 端到端覆盖；必须以真机验证错误提示与“内容可能已变化”状态。
2. **无 instrumentation/UI lifecycle 证据。** 当前 21 个 JVM 测试只覆盖 `core/`；不能证明 `enableReaderMode`、`setPreferredService`、AlertDialog 期间 tag lost、Activity pause、进程重建和 HCE service 路由。
3. **NFC/HCE 互操作仍是硬件门槛。** APDU 单测通过不等于安卓/iPhone 实机读取；`6282` EOF、分段读取、其他钱包/HCE 抢占、息屏/锁屏/后台关闭均 `awaiting_hardware`。
4. **贴纸物理失败矩阵未执行。** 只读、非 NDEF、容量不足、移开过早、回读不一致、金属/抗金属差异及每批次抽检都尚无设备/样品证据。
5. **APK 发布门槛未关闭。** 当前为 debug 测试证书；正式证书、域名根 assetlinks 合并、`/share/nfc` 关联验证、`/c/*` 不被接管、下载地址和回退仍为 `awaiting_deployment`。
6. **UI 仍在编写。** 本轮只复核现有 H5 可见代码和生成客户端；没有最终 390×844 截图、浏览器 E2E 或交互冻结证据，不将 UI 标为完成。

## 验收建议

- 软件修复/范围裁决后重跑：后端 NFC 22 例、Android 21 个 JVM 测试与 lint、H5 NFC/link 测试、`check-contract`。
- 新增并执行：临时活动贴纸正例、活动过期普通名片回退、发布工具 base 负例、H5 别名 origin 不生成 App Link、Tag 在确认对话框期间丢失的仪器/设备用例。
- 真机至少保留三表证据：HCE→安卓/iPhone、写贴纸→回读、贴纸→安卓/iPhone→短链/H5。二维码成功不得替代。

---

## 最终复查处置（2026-11-15）

上面的原始发现按只读复核时点保留，不回写成“当时已修复”。实现冻结后的复查结论如下：

**最终软件评审：`software_done`。** V1 范围内未发现剩余软件阻断；Android 真机/HCE/实体贴纸仍为 `awaiting_hardware`，生产签名、域名根 App Links 与发布仍为 `awaiting_deployment`，整体不能标 accepted。

### 原发现逐项关闭

1. **临时活动贴纸差异：已通过范围冻结关闭。**
   `docs/adr/ADR-006-手机NFC分享与双端兼容.md:19`、`tasks/nfc/角色任务卡.md:9`、`tasks/nfc/贴纸写入与采购验收.md:5` 已明确 V1 只写固定无 e 短链，活动 e 仅用于手机临时模拟。Android `TrustedLinks.kt:43` 拒绝 write+e、`apps/h5/src/utils/nfc-link.ts:35` 同样拒绝，H5 与 Android 一致；不再要求实现临时活动贴纸。

2. **活动过期无用户回退：已关闭。**
   `server/app/modules/workspace/share_link_service.py:83` 至 `:101` 现在仅在请求明确接受 HTML 时把活动失效转换为安全 404 恢复页；`:71` 至 `:79` 对目标做 HTML 转义，移除 e、保留 s，并可由 `router.py:104` 至 `:109` 返回 `no-store`、CSP 和 nosniff。JSON/API 客户端继续得到原 `NOT_FOUND`，`server/tests/api/test_nfc_share_links.py:231` 起覆盖根路径/子路径、API Accept 降级、未知卡不恢复及外部参数不进入页面。总控提供的定向结果为 **87 passed**。

3. **release base 校验不一致：已关闭。**
   `deploy/nfc/prepare_release.py:13` 至 `:33` 现在解析端口并拒绝显式端口、非法端口、非允许路径字符和双斜杠，允许集与 `apps/nfc-android/app/build.gradle.kts:8` 至 `:10` 对齐。`deploy/nfc/test_prepare_release.py:14` 至 `:16` 明确覆盖 `:443`、`:bad`、空端口、点号路径和双斜杠。本轮再次独立执行该测试：**3 passed**。

4. **NFC base/H5 别名一致性：已关闭。**
   `apps/h5/src/components/staff/NfcSharePanel.vue:13` 至 `:23` 从后端返回的 canonical short URL 构造配置地址；`apps/h5/src/utils/nfc-link.ts:43` 至 `:61` 严格校验 HTTPS、无凭据/端口/fragment、受限前缀与 code，再构造 `/share/nfc`。`apps/h5/src/pages/share/nfc.vue:12` 至 `:22` 使用与 Android 对齐的严格参数解析，并在 query 变化时 reload。H5 报告结果：**11 files / 48 tests passed，其中 NFC 9 例；lint/typecheck/build passed**。

### 跨端一致性确认

- 手机模拟：H5 从后端 canonical `s=nfc` 短链构造 emulate URL，有效活动 e 仅在明确展会场景保留。
- 贴纸写入：H5/Android/share 页均拒绝或移除 e；Android 最终写入固定 canonical `/c/{code}?s=nfc`。
- 分享来源：普通链接 `s=link`、二维码 `qr`、海报 `poster`、手机 NFC/贴纸 `nfc` 未混用。
- App Link：仅受限 `/share/nfc`；短链 `/c/*` 和普通名片 `/card/*` 不被接管。
- 失效活动：浏览器得到带普通名片入口的 HTML 404；API 保持 JSON 404，不静默伪造活动或开放跳转。
- 契约：OpenAPI SHA-256 仍为 `34240ff74f1a65f98a808c0c183bb1661fcfd2e1de3deda4d6b9f76f697570bd`，share-link required 字段及 closed schema 未漂移。

### 剩余真实阻断

以下均为证据门槛，不再作为软件整改项重复派工：

1. **手机射频未测。** 至少 3 款安卓 HCE 发送机 × 3 款安卓 + 3 款 iPhone 接收、每组合 20 次及钱包/HCE 冲突、开关/锁屏/后台/进程重建矩阵仍为 `awaiting_hardware`。
2. **实体贴纸未测。** 芯片/批次样品、只读/非 NDEF/容量不足/移开/回读不一致、金属与抗金属条件仍为 `awaiting_hardware`。
3. **生产发布未完成。** 当前 APK 为 debug 测试签名 `11547df93e8746d77a1bc888d9acf06f1e54b02582670879ec8d6e12d5722304`；正式签名、assetlinks 合并、真实域名 App Link 验证、旧站 `/c/*` 回归和下载发布仍为 `awaiting_deployment`。
4. **Tag UI lifecycle 无设备证据。** 浏览器 mock 与 JVM 测试不能证明确认对话框期间移开/换标签、锁屏、Activity rebuild 和 HCE 前台优先路由；保持上述硬件矩阵，不改冻结源码。

总控已提供浏览器 mock smoke 的 7 条断言和 4 张 390×844 截图；本轮目视核对 B4 安卓、iPhone 及 `/share/nfc` 两种 UA 状态，安卓显示模拟/固定贴纸入口，iPhone 仅显示接收说明与二维码/系统分享，没有伪报 NFC 能力。该证据属于 Web mock，不能替代任何射频结果。

报告书有一处无害陈旧记录：`tasks/reports/nfc/ui.md:30` 和 `integration.md:21` 仍保留“截图/复核进行中”的历史文字，实际截图与冻结证据已在本段记录；不影响软件结论。

