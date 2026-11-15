# AICardHub 原生 EL9 部署（T51-native）

本目录是任务 T51 的人工作业授权变体：**不使用 Docker，不启用两个 API worker**。
部署形态改为 CentOS Stream 9 / EL9 原生 systemd，API 固定一个 worker，scheduler
作为独立进程。原始 T51 的 Docker/2-worker 要求已被项目负责人明确覆盖；本 README
记录该授权。没有修改 `docs/adr/`，因为本任务只允许写 `deploy/native/**`。

- 基线提交：`fa89ef3efef230b18b1e2850f2283a82d9c0f39f`
- 契约 SHA256：`3EBE39CD03645B7C69558307F9E60097C4C2F9CCC98A327105CB630CDC64D4E2`
- 本任务没有 API 变更、数据库迁移、seed 或数据复制。
- 本目录中的脚本是**本地编写和校验**的部署材料，不代表已在生产执行。

## 1. 边界与职责

- 服务器探测、域名/证书发现、MySQL 供给、数据迁移和最终线上验收由 mainline 负责。
- 本文档只描述非敏感事实；不包含真实域名、证书路径、账号、密码、公网 IP 或密钥。
- 不覆盖、迁移或接管已有 nginx vhost、默认站点、`default_server`、全局 nginx 配置、
  SELinux 全局策略、防火墙或其他业务端口。
- 不执行 `apt`、`dnf upgrade`、盲目装包、替换系统 Python、关闭 SELinux 或打开防火墙。
- `deploy/native/evidence/marker.txt` 是先前探测留下的证据文件，未改动。

### 已确认的非敏感服务器事实

| 项 | 事实 |
|---|---|
| 系统 | CentOS Stream 9 x86_64（EL9） |
| CPU / 内存 | 4 vCPU；MemTotal 3722 MB，检查时可用 2914 MB |
| Swap | 4 GiB |
| 磁盘 | 检查时可用 52 GiB |
| 现有服务 | nginx 已有 80/443 及若干 loopback 端口；不得改动 |
| 已确认缺失 | `git`、MySQL client/server、`uv` 尚未安装 |
| 待确认 | Python 3.12 运行时、MySQL 供给、域名/证书、nginx 的 SELinux 策略 |

`uv`、Node/pnpm 和构建工具**不是生产运行时依赖**。生产不在 4 GiB 主机上拉包或构建。

## 2. 目录布局

默认根目录 `/opt/aicardhub`（可配置）：

```text
/opt/aicardhub/
├── releases/<release-id>/
│   ├── server/          # Python 源码、alembic.ini、uv.lock（只读）
│   ├── h5/              # H5 构建产物（index.html + assets/）
│   ├── admin/           # 后台构建产物（base=/admin/）
│   ├── venv/            # 预构建 Python 3.12 venv
│   └── RELEASE-METADATA
├── current -> releases/<release-id>   # 原子切换的符号链接
├── shared/
│   ├── env              # root:root 0600，systemd EnvironmentFile
│   ├── uploads/         # aicardhub:aicardhub 0755，公开的 UUID 图片
│   └── kb/              # aicardhub:aicardhub 0700，私有知识库及 .git
├── logs/                # 备份日志；应用日志走 journald
└── ops/                 # backup.sh / restore.sh / lib.sh
/var/backups/aicardhub/  # root:root 0700，私有备份
/etc/aicardhub/          # root:root 0700；backup.env、mysql-backup.cnf
```

- release 代码 `root:root`，目录 0755、文件 0644（已有执行位的脚本保留执行位）。
- `shared/env` 只能 0600；`shared/kb` 只有服务用户可进入；备份在 web root 之外。
- 服务 `umask 0022`；上传图片是设计上公开的静态资源，知识库不是。
- systemd 单元只把 `shared/uploads` 和 `shared/kb` 加入 `ReadWritePaths`。

## 3. 配置

复制 `aicardhub.conf.example` 到由 root 控制、非 secret 的位置，替换占位值：

```bash
install -m 0640 -o root -g root deploy/native/aicardhub.conf.example /etc/aicardhub/deploy.conf
$EDITOR /etc/aicardhub/deploy.conf
```

配置只允许 `KEY=value`，值不能含空白、引号、分号或 shell 元字符。它不是产品
环境文件；脚本不会 source 它。产品环境通过 `shared/env` 单独提供。

主要变量：

| 变量 | 默认/说明 |
|---|---|
| `DEPLOY_ROOT` | `/opt/aicardhub`，不能是 `/opt`、`/usr` 等保留目录 |
| `SERVICE_USER` / `SERVICE_GROUP` | 固定 `aicardhub` / `aicardhub`，系统账号、nologin |
| `RELEASES_DIR`, `SHARED_DIR`, `LOG_DIR`, `OPS_DIR` | 必须在 `DEPLOY_ROOT` 下 |
| `CURRENT_LINK` | 必须是 `DEPLOY_ROOT/current` |
| `ENV_FILE` | 必须是 `SHARED_DIR/env`，root:root 0600 |
| `UPLOAD_DIR` / `KB_DIR` | 必须是 `SHARED_DIR/uploads` / `SHARED_DIR/kb` |
| `MIGRATION_GATE_FILE` | 默认 `SHARED_DIR/migration-gate.ok`，root:root 0600 |
| `API_HOST` / `API_PORT` | API 必须绑定 `127.0.0.1`；默认端口 18000 |
| `API_WORKERS` | 固定 1 |
| `API_UNIT` / `SCHEDULER_UNIT` | `aicardhub-api.service` / `aicardhub-scheduler.service` |
| `API_MEMORY_HIGH/MAX` | 800M / 1200M 的 systemd 内存护栏 |
| `SCHEDULER_MEMORY_HIGH/MAX` | 256M / 512M |
| `SITE_NAME` / `SITE_DOMAIN` | nginx 文件名/占用域名；域名必须真实，示例值不用于生产 |
| `HTTP_LISTEN` / `HTTPS_LISTEN` | 端口或 literal host:port；不是 `default_server` |
| `TLS_CERTIFICATE` / `TLS_CERTIFICATE_KEY` | 证书/私钥绝对路径，安装前必须存在且私钥不可组/其他可读 |
| `NGINX_CONF_DIR` | 默认 `/etc/nginx/conf.d`；只新增 `${SITE_NAME}.conf` |
| `NGINX_USER` / `NGINX_GROUP` | nginx worker 账号，必须与 `aicardhub` 不同 |
| `NGINX_ACCESS_LOG` / `NGINX_ERROR_LOG` | 专用文件，默认 `/var/log/nginx/aicardhub_*.log` |
| `LOGROTATE_CONF_DIR` | 默认 `/etc/logrotate.d`，只新增专用文件 |
| `BACKUP_ROOT` | 默认 `/var/backups/aicardhub`，不得在 `DEPLOY_ROOT` 内 |
| `BACKUP_ENV_FILE` | 默认 `/etc/aicardhub/backup.env`，root:root 0600 |
| `MYSQL_DEFAULTS_FILE` | 默认 `/etc/aicardhub/mysql-backup.cnf`，root:root 0600 |
| `PYTHON_RUNTIME` | 默认 `/usr/bin/python3.12`，必须真实存在且为 3.12 |

域名、TLS 路径、监听地址和所有路径都可配置；生产渲染会拒绝 `.invalid` 和
`REPLACE...` 占位值。

## 4. 先决条件

生产主机必须具备：

- EL9 x86_64；本方案不提供 Ubuntu/Debian 安装器。
- **Python 3.12 运行时**，与预构建 venv 的 ABI 匹配；3.9/3.11 不可替代。
- `git`（知识库 `app/kb/store.py` 在运行时执行本地 Git 提交）。
- MySQL 8 服务与仓库；`mysqldump`（备份）和备份账号由 mainline 供给。
- 现有 nginx（含 `conf.d` include）、systemd、curl、tar、gzip、sha256sum、flock、
  `ss`、`getent`、`useradd/groupadd`、`install`、`stat`。
- SELinux Enforcing 时还需要 `matchpathcon`、`semanage`（通常
  `policycoreutils` / `policycoreutils-python-utils`）；具体包名由操作者按 EL9
  仓库确认。
- 域名和证书由 mainline 发现/提供；本目录只使用占位路径。

已知当前缺失 `git`、MySQL client/server、`uv`；Python 3.12 版本待确认。脚本会
在 preflight 中明确失败/告警，不会自行装包。生产不安装 `uv`/Node/pnpm，也不执行
`uv sync` 或 `pnpm build`。

## 5. 预构建 release 契约

release 必须在与生产相同 ABI 的 EL9 x86_64 + Python 3.12 环境构建（CI 或临时构建机），
默认不在生产机构建。目录根部必须包含：

```text
server/   app/、alembic/、alembic.ini、pyproject.toml、uv.lock
h5/       index.html、assets/
admin/    index.html、assets/（Vite base=/admin/）
venv/     bin/python、pyvenv.cfg、依赖
```

建议用 `python3.12 -m venv --copies` 生成可搬移 venv，再把锁文件依赖离线安装进去。
systemd 使用 `venv/bin/python -m uvicorn ...`，不依赖 venv 里脚本的 shebang，因此
release 目录可原子改名/切换。venv 中只允许指向 release 内部的相对符号链接。

`validate_artifact.py` 会拒绝：

- 绝对路径、`..`、hardlink、设备/FIFO、setuid/setgid；
- 绝对或逃逸的符号链接，以及“先建符号链接再写其子路径”的归档；
- `.git`、`node_modules`、`.env*`、`local-credentials.json`、`*.credentials.local.json`、
  SQLite/DB 文件；
- 缺少 `server/app/main.py`、`server/app/scheduler.py`、`alembic.ini`、`uv.lock`、
  `h5/index.html`、`admin/index.html`、`venv/bin/python` 等必需项。

## 6. 本地渲染与校验

不需要数据库、secret 或真实域名：

```bash
cd deploy/native
python3 scripts/render.py --check --config aicardhub.conf.example
python3 scripts/render.py --config aicardhub.conf.example --out /tmp/aicardhub-render
python3 scripts/validate.py --config aicardhub.conf.example --render-dir /tmp/aicardhub-render
bash scripts/verify-local.sh
```

Windows 上可用 Git Bash 执行最后一条；本任务没有在 Windows 上运行 `nginx -t` 或
`systemd-analyze verify`。`render.sh` 只是 stdlib 渲染器的薄包装；默认只渲染，不改主机。

## 7. 首次部署顺序

所有主机命令以 root 执行，且先完成配置校验。每一步都可重复执行，但不会覆盖
未带生成标记的文件、不会覆盖已存在的 `shared/env`、不会自动采用既有目录/账号。

### 7.1 校验配置与主机

```bash
cd deploy/native
py=/usr/bin/python3.12
$py scripts/render.py --check --config /etc/aicardhub/deploy.conf
scripts/preflight.sh --config /etc/aicardhub/deploy.conf --mode install --require-tls
```

`--mode render` 可在无 root、无真实证书的机器上运行。`--mode install` 会检查 EL9、
Python 3.12、git、nginx、端口、磁盘、SELinux、证书/私钥和已有文件归属。

### 7.2 创建账号和目录

```bash
scripts/bootstrap.sh --config /etc/aicardhub/deploy.conf --apply
```

创建 `aicardhub` 系统组/用户、release/shared/logs/ops 目录、私有 kb 和备份根。
如果同名账号/目录已存在但属性不符，脚本会停止，不会“接管”。

### 7.3 安装 unit、运维脚本，可选 nginx/logrotate

先安装 API/scheduler unit 和 ops 脚本：

```bash
scripts/install.sh --config /etc/aicardhub/deploy.conf \
  --env-file /secure/out-of-band/aicardhub.env \
  --install-units --install-logrotate
```

- `--env-file` 只在目标不存在时复制为 root:root 0600；已有 live env 永不覆盖。
- unit 安装后只 `daemon-reload`，不 enable、不 start。
- `--install-nginx` 才会安装专用 vhost 并运行 `nginx -t`；`--reload-nginx` 才 reload。
  建议在 API 激活并验证后再执行 nginx 安装/重载。
- `--install-backup-timer` 只安装 backup service/timer，不 enable；需要先配置
  `backup.env` 和 MySQL defaults 文件。

### 7.4 迁移门禁（mainline 所有）

本任务不运行 Alembic、不迁移、不 seed、不复制数据。mainline 在批准的迁移窗口完成
数据库准备后，写一个 root:root 0600 的门禁文件，例如：

```text
release_id=20261115-01
schema_compatible=yes
alembic_revision=<approved-revision>
approved_by=<mainline-role>
approved_at=<UTC>
```

`activate.sh` 要求 `release_id` 与本次 release 完全一致、`schema_compatible=yes`、
revision 非空、`approved_by` 非空。门禁是激活前置条件，不是迁移脚本。

### 7.5 安装 release

```bash
scripts/release.sh --config /etc/aicardhub/deploy.conf \
  --artifact /secure/releases/aicardhub-20261115-01.tar.gz \
  --release-id 20261115-01
```

脚本校验归档、安全解包、验证 venv 为 3.12、写 `RELEASE-METADATA`、递归设为
`root:root` 和只读，最后把 staging 原子改名为 `releases/<id>`。默认不切换 current，
不启动服务。旧 release 不会删除。

### 7.6 激活与健康门禁

```bash
scripts/activate.sh --config /etc/aicardhub/deploy.conf --release-id 20261115-01
```

流程：校验 env/门禁/SELinux → 原子切换 `current` → enable/restart API 和 scheduler →
轮询 `http://127.0.0.1:<API_PORT>/health` 最多 30 秒 → 检查 scheduler 存活。失败时
自动切回旧 release 并重启；首次部署失败则停止 unit 并移除 current。不会 reload nginx，
不会回滚数据库。

### 7.7 安装/重载 nginx

```bash
scripts/install.sh --config /etc/aicardhub/deploy.conf --install-nginx --reload-nginx
```

`nginx -t` 通过才 reload；失败会恢复安装前的 vhost 文件且不 reload。只新增
`NGINX_CONF_DIR/${SITE_NAME}.conf`，不碰 `nginx.conf`、默认站点或其他 vhost。

验证：

```bash
ss -ltnp 'sport = :18000'          # 应只有 127.0.0.1:18000
curl -fsS http://127.0.0.1:18000/health
journalctl -u aicardhub-api -u aicardhub-scheduler -n 100 --no-pager
```

线上 H5、`/staff` 嵌套路由、`/admin` 嵌套路由、`/api`、`/c/`、SSE 逐字输出和真实
上传需在 EL9 + 浏览器中另行验收；本任务未执行。

## 8. nginx vhost 说明

模板：`templates/nginx/aicardhub.conf.in`。渲染后只含两个 server（HTTP→HTTPS 和
HTTPS），**没有 `default_server`**。

- `/`、`/card/*`、`/chat/*` → H5 `index.html` fallback；`/staff` 及 `/staff/**` 用同一份
  H5 构建。
- `/admin` 301 到 `/admin/`；`/admin/**` 用 `admin/index.html` fallback；
  `/admin/assets/**` 单独长缓存。后台 Vite 生产 base 是 `/admin/`。
- `/api/` 和 `/c/` 反代到 loopback upstream；所有 `/api/` 都关闭
  `proxy_buffering`、`proxy_request_buffering`、`proxy_cache`，HTTP/1.1，读写超时
  120 秒，覆盖访客对话和员工测试对话两条 SSE 路径。
- `client_max_body_size 20m`；只在本 vhost 开启 gzip。
- 限流只作用于本 vhost：API 8 r/s、burst 16、每 IP 20 连接；不修改其他 vhost。
- `/files` 只允许应用生成的 UUID 派生名：
  - 32 位小写 hex 照片 `.jpg`，或同名前缀 `-bg.jpg`；
  - 32 位小写 hex 的 `-wechat.png`；
  - 名片码（1–32 位小写字母/数字）+ 10 位 hex 的 `-qr.png` / `-poster.jpg`。
  正则大小写敏感，扩展名必须小写；`/files/.env`、`/files/foo.php.jpg`、大写
  `.JPG`、带路径段的名字都落到前缀 fallback `return 404`。该 fallback 不是
  `try_files`、不是 proxy、不会落到 API 的 `StaticFiles /files`。
- 符号链接由 `disable_symlinks on` 拒绝；`limit_except GET` 拒绝非 GET/HEAD。
- dotfile/dot-directory 在本 vhost 全部 404；nginx 从不 serve `shared/kb`、`shared/env`
  或 `/var/backups/aicardhub`。
- TLS 证书/私钥、域名、监听端口都是变量；不假设证书位置。

nginx worker 用户与 `aicardhub` 分离；不要给 nginx 加 `aicardhub` 组，上传目录使用
公开图片所需的 0755/0644，知识库保持 0700。本配置不写全局 `user` 指令。

## 9. EL9 SELinux

先检查：

```bash
getenforce
ls -Zd /opt/aicardhub /opt/aicardhub/shared/uploads /opt/aicardhub/shared/kb
semanage port -l | grep 18000
```

Enforcing 时，preflight/activate 会要求：

1. nginx 可读 `/opt/aicardhub/releases/<id>/h5`、`.../admin` 和 `shared/uploads`；
2. loopback API 端口被允许；
3. `matchpathcon` 与 `semanage` 可用。

建议的**窄范围**操作（由操作者执行；脚本不会自动改策略）：

```bash
semanage fcontext -a -t httpd_sys_content_t '/opt/aicardhub/shared/uploads(/.*)?'
semanage fcontext -a -t httpd_sys_content_t '/opt/aicardhub/releases/[^/]+/h5(/.*)?'
semanage fcontext -a -t httpd_sys_content_t '/opt/aicardhub/releases/[^/]+/admin(/.*)?'
restorecon -Rv /opt/aicardhub/shared/uploads /opt/aicardhub/releases
semanage port -a -t http_port_t -p tcp 18000   # 若已存在则先查，不要重复添加
```

不要用 `setenforce 0`、不要全局关闭 SELinux、不要默认开启范围过宽的
`httpd_can_network_connect`。若出现 AVC，用 `ausearch -m AVC -ts recent` 诊断并只加
最小本地策略。标签/端口未满足时部署脚本会 abort，操作者完成上述步骤后重跑。

## 10. 备份与恢复

### 备份

`backup.env.example` 复制为 `/etc/aicardhub/backup.env`（root:root 0600）；
`mysql-backup.cnf.example` 复制为 `/etc/aicardhub/mysql-backup.cnf`（root:root 0600）。
备份账号由 mainline 供给，最小权限，推荐 `SELECT, SHOW VIEW, TRIGGER, EVENT`，
是否还需要其他权限由 DBA 按 MySQL 8 实例确认。密码只在这份 defaults-extra-file，
不进入命令行、环境变量或日志。

手动备份：

```bash
/opt/aicardhub/ops/backup.sh --config /etc/aicardhub/backup.env
```

行为：

- 先校验命令、私有配置和目录，再创建任何输出；
- 获取与部署共用的 `/run/aicardhub-*.lock`；
- 停止 scheduler，再停 API；EXIT trap 保证失败/成功后都尝试按 API→scheduler 重启；
- `mysqldump --single-transaction --quick --routines --events --triggers
  --set-gtid-purged=OFF --no-tablespaces --databases <db>`；
- 打包 `uploads`、整个 `kb`（含 `.git`）和受保护 `env`；
- 校验 dump 完成标记、tar 成员、SHA256SUMS；
- 以 0700 目录、0600 文件原子发布为 `aicardhub-backup-<UTC>`；
- 只清理自己命名模式下的、超过 14 天的完成备份和自己遗留的 partial；
- 不打印 dump 内容、不把密码放到 argv/env、不把归档放进 web root。

`install.sh --install-backup-timer` 只安装 service/timer（默认 02:30，随机延迟 15 分钟，
`Persistent=true`），不会 enable。操作者确认配置后：

```bash
systemctl enable --now aicardhub-backup.timer
systemctl list-timers aicardhub-backup.timer
```

### 恢复

`restore.sh` 只做验证和打印步骤，不执行恢复：

```bash
/opt/aicardhub/ops/restore.sh --config /etc/aicardhub/backup.env \
  --backup-dir /var/backups/aicardhub/aicardhub-backup-...
```

它会校验 0700/0600、SHA256SUMS、dump 完成标记和 tar 成员名，然后打印：

1. 先做新的备份并记录变更窗口；
2. 停止 scheduler/API；
3. 用同一 0600 defaults-extra-file 执行 `mysql ... < database.sql`；
4. 只解包 `uploads`、`kb` 到 shared；`env` 仅在确实要回滚凭据时单独解包；
5. 修正 `aicardhub:aicardhub` 所有权；Enforcing 时 `restorecon`；
6. 启动 API→scheduler，检查 health 和 journal。

数据库恢复不可逆，必须由 mainline/操作者按授权执行。备份包含私密 `env` 和知识库，
归档本身必须 0600，离机副本必须加密并放在受控私有位置；不要生成公开下载链接。

## 11. 日志

- API/scheduler 的 stdout/stderr 进入 **journald**。用
  `journalctl -u aicardhub-api -u aicardhub-scheduler` 查看。不要为了“有文件可转”
  而伪造空应用日志；本目录不修改 journald 全局策略/保留期。
- nginx 使用专用 `NGINX_ACCESS_LOG` / `NGINX_ERROR_LOG` 文件。
- 备份写 `BACKUP_LOG`。
- `templates/logrotate/aicardhub.conf.in` 只轮转上述专用 nginx 文件和备份日志；
  nginx 日志 `kill -USR1` 重新打开，不重启全局 nginx。应用 journald 由主机策略管理。
- 先把 `*.log` 安装/生成后再启用 logrotate；不要给不存在的应用日志造空轮转。

## 12. 内存预算与非功能边界

4 vCPU / 约 3.6 GiB RAM 的主机需要同时容纳 MySQL、nginx、一个 API worker 和
一个 scheduler。默认 systemd 护栏：

- API `MemoryHigh=800M`、`MemoryMax=1200M`；
- scheduler `MemoryHigh=256M`、`MemoryMax=512M`；
- `TasksMax` 256/128，`LimitNOFILE=65536`；
- 不在主机构建前端/venv，不并行跑全量测试，不启动第二个 worker 或 scheduler。

这些值是保守护栏，不是实测峰值；上线后应观察 `systemctl status`、`journalctl`、
`free -m`、`ss -ltnp` 和 MySQL 内存。若 OOM，先减小 MySQL 缓冲/连接数或按实测调整
护栏，不要增加 worker。

## 13. 回滚

```bash
scripts/rollback.sh --config /etc/aicardhub/deploy.conf --to <previous-release-id>
```

- 目标 release 必须仍在 `releases/`；
- 门禁文件必须改写为目标的 `release_id` 并确认 schema compatible；
- 原子切换 current，重启 API/scheduler，跑同样的 30 秒 health 和 scheduler 检查；
- 失败则切回原 current 并重启；
- **不会反向执行数据库迁移**。如果新 schema 与旧代码不兼容，mainline 必须决定
  向前修复而不是回滚，门禁就是该判断的落点。

## 14. 本次未验证 / 风险

- 没有在生产或任何 Linux 主机执行 `nginx -t`、`systemd-analyze verify`、
  `systemctl start`、SSE 逐字验收、上传、MySQL dump 或 restore。
- Python 3.12 运行时、MySQL 供给、域名/证书、nginx SELinux 策略仍未确认。
- `git`、MySQL client/server、`uv` 当前缺失；`uv` 缺失不影响运行时，但 `git` 缺失
  会阻断知识库写入。
- 本地验证使用 Windows Python 3.13 + Git Bash 的 stdlib 渲染/语法检查；渲染器代码
  兼容 3.12，未在 EL9 Python 3.12 下执行。
- `scripts/check.sh` 未运行：它需要数据库、secret 和完整前后端环境，本任务未准备，
  且不属于部署材料验证。
- 没有 API 变更或数据库迁移；契约哈希见文首。
