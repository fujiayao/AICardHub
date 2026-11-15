# NFC UI 交付报告（H5 + 后台）

marker: ui-agent-start 2026-11-15（写入/读回闭环通过）。模型路由 claude-2/claude-opus-5-5；工作区 worktrees/nfc-implementation，分支 feat/nfc-implementation，基线 d9014ad，未 commit。

## 契约与生成
- contracts/openapi.json SHA256 `34240ff74f1a65f98a808c0c183bb1661fcfd2e1de3deda4d6b9f76f697570bd`（只读）。
- H5：`scripts/endpoints.mjs` 新增 `cardShareLink` → `GET /api/v1/me/card/share-link`；`pnpm generate:api` 生成 46 operations。
- Admin：`pnpm gen:api` 生成 53 operations（未手改）。再生成后 NoteInput.description 变为必填，`src/api/adapters/index.ts` saveNote 补 `description: ""` 默认值以通过 typecheck（适配层最小修正）。

## 完成内容
- B2 `pages/staff/card/index.vue`：「NFC 功能未启用」改为「手机分享 · NFC 碰一碰与写贴纸」，跳 `/staff/card/share?tab=nfc`。
- 我的 `pages/staff/me.vue`：唯一 NFC 行改为「NFC 分享」，说明实物卡库存与挂失暂缓，跳实际分享入口。
- B4 `pages/staff/card/share.vue` 重构为组合页：基础数据只取 card + campaigns；二维码/海报（`ShareMediaPanel`，原 /share 接口，图片失败只影响该 tab）、链接（`ShareLinkPanel`，轻量 share-link s=link）、手机 NFC（`NfcSharePanel`）分别加载，字体缺失不阻断 NFC。支持 `?tab=nfc`。竞态沿用 useResource revision。
- `NfcSharePanel`：手机模拟链接 s=nfc 保留有效 e；贴纸链接 s=nfc 永不带 e。App Link 由后端返回的短链解析受信任 origin+前缀构造 `/share/nfc?code=&mode=`，不用 window.origin。后端短链非 HTTPS/带端口/凭据/fragment/非法前缀/额外参数时按钮禁用并说明原因；复制完整 NFC 链接照常可用。iPhone 只显示接收说明 + 二维码/系统分享；微信内/非安卓给出指引；不检测安装、不宣称检测到 NFC，文案为「按系统提示操作」，不承诺必然打开。
- `NfcInstallHelp`：`VITE_NFC_APK_URL` 可选（仅 https 无凭据）；未配置显示「调试中未发布，联系管理员」。`.env.example` 已补空值说明。
- 公开 `pages/share/nfc.vue`：仅调 publicCard 预览，不调 visit/visitor 接口（不计访问）；严格解析与原生一致：code `^[A-Za-z0-9_-]{1,32}$`，mode 缺省 emulate、`''`/未知值报错，e 仅 `^[1-9][0-9]*$` 且 safe integer、拒绝数组，write+e 拒绝，额外参数拒绝；监听 query 变化重新加载。说明自有 HTTPS 域名要求。
- `platform/index.ts`：新增 `isAndroid`（仅用于选择说明文案）与 `openAppLink`（用户点击跳转）。
- 工具 `utils/nfc-link.ts` + `tests/nfc-link.test.ts`（9 例：根路径与 /aicardhub 前缀、write 无 e、http/端口/凭据/fragment/非法前缀/非法 % 编码（URIError）/额外参数负例、中文/冒号/百分号/点 code 负例、1e2/['1']/前导零 e 负例、APK URL）。全局 `sceneCampaign` 未改。
- 后台 `views/Scope.vue`：NFC 拆为手机 NFC 分享（调试候选）、贴纸写入（调试候选）、实物卡库存/绑定/挂失（暂缓）；注明安装包未发布、iPhone 仅接收、无已验证真机、来源为渠道归因；「后续原计划功能」面板未改；菜单文案「交付范围 / NFC」已符合，未改。

## 修改文件
apps/h5：scripts/endpoints.mjs、src/api/generated/*（生成）、.env.example、src/platform/index.ts、src/utils/nfc-link.ts、src/components/staff/{NfcSharePanel,ShareMediaPanel,ShareLinkPanel}.vue、src/components/common/NfcInstallHelp.vue、src/pages/staff/card/{index,share}.vue、src/pages/staff/me.vue、src/pages/share/nfc.vue、tests/nfc-link.test.ts。
apps/admin：src/api/generated/*（生成）、src/api/adapters/index.ts、src/views/Scope.vue。新文件均 ≤300 行，无颜色字面量。

## 检查结果
- H5：`pnpm lint` 通过；`pnpm test` 11 files / 48 tests 通过（其中 nfc-link 9 例）；`pnpm build`（含 vue-tsc）通过。
- Admin：`pnpm lint`（eslint + prettier）通过；`pnpm typecheck` 通过；`pnpm build` 通过（仅既有 chunk >500kB 警告）。
- 未运行 scripts/check.sh 全量（后端/安卓不在本角色范围）。

## 截图
- 未完成。tasks/reports/screenshots/nfc 尚未生成；总控已表示可代做。建议 390×844：B2、B4 NFC tab（安卓/iPhone UA）、B4 后端短链为 http 时的禁用态、/share/nfc 正常与无效参数、后台 Scope。截图仅为 UI 自动化模拟，不是射频证据。

## 风险 / 需要确认
- 无手机/贴纸射频证据；App Link 实际唤起依赖总控发布 assetlinks 与 APK 签名。
- 活动 e 失效时 /c 的回退页由后端 owner 处理。

## 总控补充核验

最终集成check.ps1通过；H5测试JSON确认NFC9例包含于48总例。另行admin tests27通过。总控已补4张390宽模拟截图及后台Scope截图，路径tasks/reports/screenshots/nfc，7条Web mock smoke断言通过。图片生成失败与NFC独立加载、canonical域名入口、iPhone指导、配置页无visit均核验；无RF证据。
