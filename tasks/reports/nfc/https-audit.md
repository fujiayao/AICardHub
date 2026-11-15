# NFC HTTPS 发布只读审查

日期：2026-11-16，Asia/Shanghai。执行方式：当前 Codex 原生子代理；未经过 Magpie、未调用其他模型或 CLI。权限：只读远程状态和本地部署脚本，仅写本报告。

## 已核验现状

- 现有私有连接入口：主仓 `.local/deploy-private/remote.py`，通过 `connect()` 建立 Paramiko SSH 连接；`ssh.json` 供进程读取，`host-key.json` 做固定指纹校验。可由总控直接 import 后复用，不能复制凭据到命令、报告或新源码。
- 实际线上版本：`/opt/aicardhub/current` 指向 `/opt/aicardhub/releases/919589c2555e`。
- `nginx`、`aicardhub-api`、`aicardhub-scheduler`、`aicardhub-db` 均 active。
- HTTPS 根站、`/aicardhub/staff/login`、`/aicardhub/admin/` 均返回 200。
- `/aicardhub/api/v1/health` 返回 200，`status=ok`、`llm_mode=openai`，实际模型为 `gpt-6.1-terra`。这是已部署的真实运行配置，不能用本地验收 `LLM_MODE=fake` 覆盖。
- 线上环境非秘密字段为 `APP_ENV=production`、`PUBLIC_BASE_URL=https://haiwex.com/aicardhub`、`AICARD_ROOT_PATH=/aicardhub`；API 和 scheduler 都从 `/opt/aicardhub/shared/env` 读取配置。
- 线上 `/api/v1/me/card/share-link` 返回 404，当前 router 未找到 share-link/resolve_short_link，确认本次新后端仍需发布。
- 域名根 `/.well-known/assetlinks.json` 返回 200，但 Content-Type 为 HTML、1079 字节，与根站相同，是现有 `/` 代理 fallback，不是有效 Android App Links 文件。
- 已查询的 `/var/www/haiwex-acme/.well-known/assetlinks.json`、`/opt/aicardhub/shared/assetlinks.json`、`/opt/aicardhub/ops/nginx/assetlinks.json` 不存在。发布时仍应先导出现有 nginx 完整配置确认其他 include，不将 HTML 200 当作可合并 JSON。
- 当前 API 固定 loopback 18000，systemd 通过 current/server 与 current/venv 执行；Python 实际在 `/opt/aicardhub/shared/python/cpython-3.12.16-linux-x86_64-gnu/`。

## 最小更新建议

1. 总控唯一执行远程写入。先保存 `readlink -f current`、当前 release manifest、`relay-ip.conf` 与应用 locations include，并对现有数据库按项目备份流程做应用范围备份。不要修改或导入本地 `.env`、测试数据库、seed 演示资料。
2. 本地从当前 NFC 工作分支构建 H5（base `/aicardhub/`）和后台（base `/aicardhub/admin/`）；H5 APK URL 指向将真实提供的 HTTPS 下载路径。只打包跟踪的 server/scripts/deploy、构建 dist 和发布 APK/metadata。排除 `.local`、私钥、账号文件、数据库、知识原始资料。
3. 在新 release 目录准备源码和两个 dist。NFC 后端无迁移、无新增 Python 依赖：保留共享 env、uploads、kb 与现有 Python 依赖。可以复制现有 venv 保持独立回退；若链接到旧 venv，必须显式记录其路径、确保回退和清理时不删除被引用旧 release。不要因代码更新重新安装/升级系统包。
4. 上传后核对文件 SHA-256、Python import、OpenAPI 中新 operation，以及静态资源 base。发布前使用 loopback stage 或独立临时 API 端口验证新源码且不替换运行环境；无迁移时不运行 seed，不重新导入业务库。
5. 增加严格限定的下载和域名关联位置，建议纳入现有 `/opt/aicardhub/ops/nginx/aicardhub.locations.conf`：
   - `location = /aicardhub/downloads/aicardhub-nfc.apk`，精确 alias 到独立发布 APK，GET/HEAD、APK MIME、nosniff；不开放任意目录。
   - `location = /.well-known/assetlinks.json`，精确 alias 到应用受控 JSON，`application/json`、无登录、无重定向；GET/HEAD、nosniff。
   - 保留旧站 `/`、`/api`、`/cpa`、`/static` 等所有现有代理以及 ACME 路径。当前 TLS server 在 `relay-ip.conf` 第67行 include 应用 locations，故可将以上精确位置加入该 include，而不改根 `/` 的含义。
6. 将 Android owner 实际 release APK 的包名与签名 SHA-256 写入 assetlinks。仅关联 Manifest 中 `/aicardhub/share/nfc`；不要关联 `/c/*` 或 `/card/*`。正式签名私钥不上传 web root。
7. `nginx -t` 通过后原子切 current 到新 release，重启 API 和 scheduler，再 reload nginx。失败立刻切回原 current、还原 include 并重启服务；shared env 与数据均保持原样。
8. HTTPS 实际检查：根站仍200；健康仍openai；员工真实登录、share-link返回HTTPS带`s=nfc`且无e长期贴纸；短链302前缀正确；H5 NFC页可点打开/下载；APK内容/哈希/签名正确；assetlinks必须JSON200；配置入口能preview；现有访客名片、vCard、图片、后台和真实对话保持可用。

## 连接调用形态

总控可使用 Python `importlib.util.spec_from_file_location` 加载原有私有 `remote.py`，通过 `with module.connect() as client` 及 `client.exec_command`、`open_sftp` 实施。原 CLI 也支持 `--command-file`、`--upload`、`--download`；任务正文用文件避免 shell 拼接。不要重放 `start-api.sh`（它要求 current 不存在），不要重放早期数据库初始化或全量迁移脚本。

## 仍需真机

服务器正确部署和 App Links JSON 可达不等于手机射频验收通过。用户安装 release APK 后验证安卓手机模拟→安卓/iPhone、写贴纸→回读，以及贴纸→安卓/iPhone。原生 Android 同源浏览器点击 App Link 可能留在浏览器，UI/Android owner 正协调显式 Android intent 用户点击入口；域名关联与实际设备仍需一起核验。

本报告没有修改服务器或生产数据，也没有修改产品实现。

## 发布后最终 HTTPS 只读核验（2026-11-16）

总控发布后，本代理通过当前 Codex 直接进行公网 HTTP 和只读 SSH 复核，没有通过 Magpie，也没有远程写入或创建账号。

| 项目 | 实测结果 |
| --- | --- |
| 当前 release | `/opt/aicardhub/releases/nfc-20261116` |
| `nginx -t` | syntax ok / successful |
| 服务 | nginx、aicardhub-api、aicardhub-scheduler、aicardhub-db、new-api、cliproxyapi 全部 active |
| 根站 `/` | 200，1079字节 HTML，原有根站未被 NFC 路径替换 |
| HTTPS health | 200，status=ok，llm_mode=openai，model=gpt-6.1-terra |
| 未登录 share-link | 401 JSON，路由已存在，已从原404更新为正确鉴权响应 |
| `/.well-known/assetlinks.json` | 200、application/json、无重定向，已替换原 HTML fallback |
| APK 下载 | 200、application/vnd.android.package-archive、664216 bytes，ZIP/APK magic `504b0304` |
| APK SHA-256 | `6bdb83bf035366aa2117e48d16ec5ec440bd7d1ef7833888383d103f08aa998c`，与总控提供 release 值一致 |
| 假下载路径 | `/aicardhub/downloads/not-present.apk` 返回404，不进入SPA fallback |
| 私有路径 | `/aicardhub/.env` 和 `/aicardhub/server/.env` 均404 |
| 普通短链1 | GET `/aicardhub/c/5dbb1d43?s=nfc` 为302，Location=`/aicardhub/card/5dbb1d43?s=nfc`，no-store、Vary:Accept |
| 普通短链2 | GET `/aicardhub/c/ffe358d1?s=nfc` 为302，Location=`/aicardhub/card/ffe358d1?s=nfc`，no-store、Vary:Accept |
| 跟随短链 | 两个短链最终H5均200，保留部署前缀与来源 |

assetlinks 实际内容匹配包名 `cn.aicardhub.nfc`，namespace `android_app`，relation `delegate_permission/common.handle_all_urls`，证书 SHA-256：

```text
6D:5B:A4:2E:B8:FD:D4:BD:9F:7B:9E:9E:E5:E0:6C:F6:5A:92:59:DA:13:F2:97:95:93:08:EA:E9:96:18:1A:18
```

只读 SSH 用 `importlib.util.find_spec('app')` 确认应用模块来源为新 release 的 `server/app/__init__.py`，新 `share_link_service.py` 文件存在，router 含 `me_card_share_link`。nginx include 已添加精确 assetlinks 和 APK alias，其他 downloads 请求固定404。

一次直接导入 `share_link_service` 的只读探针未加载生产 EnvironmentFile，因缺数据库和 JWT 环境字段而失败；这是审查探针没有服务环境的限制，不是运行服务故障。随后改为无环境的模块路径查找确认来源；线上 health 与真实服务状态正常。另以 HEAD 测短链返回405（路由仅GET）后，已使用实际GET确认302，不把HEAD结果误报为短链失败。

最终结论：**HTTPS 发布基础设施及公开 NFC 入口通过本轮只读核验**。员工真实登录及页面交互由总控另行执行；后台 menu 正在单独更新，不将期间旧文案作为基础部署失败。手机域名关联实际唤起、安卓/iPhone碰触、贴纸写入及回读仍待用户真机验收，本报告不将公网200或JSON可达当作射频通过。
