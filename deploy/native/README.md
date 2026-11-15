# AICardHub 原生 EL9 部署运行手册

本目录只提供 AICardHub 在**现有** nginx TLS 站点中挂载 `/aicardhub` 前缀的部署材料。
公开入口固定为 `https://haiwex.com/aicardhub`。不在本机创建独立 vhost、TLS 站点或
公网监听，不修改其他站点和主机根路径；生产以 mainline 的现有 nginx、证书、MySQL 和 systemd 为准。

本包是本地编写的交付材料，最终校验由 supervisor 在实现结束后单独执行并记录，不代表已在
生产执行，也不代表完整验证已通过。旧 `fa89ef3` 构建产物不可部署；最终
artifact 必须从当前 mainline 重新构建，包含 backend 前缀/字体修复 `97f3b82`、`ce33cab`
和 frontend 前缀集成 `596248b`、`c42365f`。

## 1. 固定部署契约
- 生产 nginx 只使用 server 上下文 include：
  `/opt/aicardhub/ops/nginx/aicardhub.locations.conf`。该 include 不含 `server`、
  `listen`、`root`，所有 location 都限定在 `/aicardhub`。
- H5 和后台 SPA 的 history fallback 使用 `error_page 404 =200`，深链接返回 200；
  `/assets/**` 缺失文件仍为 404，不回退、不代理。
- `/aicardhub/api/` 和 `/aicardhub/c/` 反代到 loopback API，剥离 `/aicardhub` 前缀；
  SSE 关闭 buffering/cache，读、写、发送超时均为 120 秒。
- `/aicardhub/.git`、`/aicardhub/admin/x/.env` 等任意层级点路径由最前面的引号正则
  `^/aicardhub/(?:.*/)?\.` 拒绝。
- `/aicardhub/files/` 只接受应用生成的 UUID 派生图片名；该 uploads 正则保留
  `disable_symlinks on`，其他名称固定 404。
- release 静态资源来自 `current/apps/h5/dist` 和 `current/apps/admin/dist`；因为
  `current` 是有意保留的符号链接，静态资源 location 不使用 `disable_symlinks`。
- API 固定 loopback `127.0.0.1:18000`、一个 worker，systemd 使用
  `--root-path /aicardhub`；scheduler 是独立进程，不在 API 启动时启动。
- 可选 stage wrapper 只监听 `127.0.0.1:18080`，复用同一 include，无 TLS，不对外。

## 2. 主机前置
- EL9 x86_64；mainline 现有 Python 3.12、MySQL 8、git 和 nginx。本包不远程复核这些
  事实，preflight 会再次检查；生产运行时不需要 `uv`。
- 需确认现有 Linux 运行时依赖、CJK 字体和 SELinux 策略；不执行 `apt`/`dnf`
  升级或安装，不关闭 SELinux，不改防火墙。
- release 必须预先在与生产相同的 EL9 x86_64 + Python 3.12 环境构建。生产机不拉包、
  不构建前端、不创建 venv。
- 数据迁移、数据库账号、证书和 secret 由 mainline 供给；README 不含账号、密码或公网 IP。

## 3. 目录、账号与权限

默认根目录为 `/opt/aicardhub`：

```text
releases/<id>/server/             Python 源码、alembic、锁文件
releases/<id>/apps/h5/dist/       H5 构建产物
releases/<id>/apps/admin/dist/    后台构建产物
releases/<id>/venv/               Python 3.12 运行时（release 前置）
current -> releases/<id>          原子切换
shared/uploads/                   公开图片，独立于 kb
shared/kb/                        私有知识库，含 .git
shared/env                        root:root 0600 EnvironmentFile
ops/nginx/                        渲染后的 include 和可选 stage wrapper
logs/                             备份日志；应用日志进 journald
```

- release 代码 `root:root`、目录 0755、文件 0644，服务身份不能写 release。
- `shared/uploads` 用于公开图片；`shared/kb` 对服务用户 0700，包含 `.git`，不得放到 web root 或日志目录。
- `shared/env` 必须 `root:root 0600`，由 systemd `EnvironmentFile` 读取；不要用 shell
  source，不要把 secret 写进 unit 或命令行。
- `/var/backups/aicardhub` 和 `/etc/aicardhub` 由 root 管理，归档 0700/0600。

## 4. 应用环境

按 `templates/app.env.example` 由 root 在带外创建 `shared/env`，至少确认：

```text
PUBLIC_BASE_URL=https://haiwex.com/aicardhub
AICARD_ROOT_PATH=/aicardhub
AICARD_POSTER_FONT_PATH=/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc
```

字体路径必须按目标主机实际安装、可读的 CJK 字体确认或替换；示例不声明字体已安装。
数据库、JWT、LLM 等 secret 只通过受控渠道注入。

## 5. 渲染、预检、引导和安装

配置模板为 `aicardhub.conf.example`；复制到 root 控制的非 secret 位置后修改：

```bash
cd deploy/native
python3 scripts/render.py --check --config /etc/aicardhub/deploy.conf --production
scripts/preflight.sh --config /etc/aicardhub/deploy.conf --mode render
sudo scripts/preflight.sh --config /etc/aicardhub/deploy.conf --mode install
```

首次创建账号和目录；先 dry-run，再应用：

```bash
sudo scripts/bootstrap.sh --config /etc/aicardhub/deploy.conf
sudo scripts/bootstrap.sh --config /etc/aicardhub/deploy.conf --apply
```

安装 unit、运维脚本和专用 logrotate；installer 只把 include/stage 渲染到
`OPS_DIR/nginx`，不编辑 `nginx.conf`、不写 `conf.d`、不执行 `nginx -t`、不 reload：

```bash
sudo scripts/install.sh --config /etc/aicardhub/deploy.conf \
  --env-file /secure/out-of-band/aicardhub.env \
  --install-units --install-logrotate
```

需要每日备份时，先准备 `backup.env` 和 MySQL defaults 文件，再加
`--install-backup-timer`；该选项只安装，不 enable timer。

## 6. 接入现有 TLS nginx（必须人工）

只把下面一行放进**现有 haiwex.com TLS server 块**，不要放进 `http` 上下文的
`conf.d/*.conf`：

```nginx
include /opt/aicardhub/ops/nginx/aicardhub.locations.conf;
```

插入位置必须在现有通用 regex、静态或脚本 location 之前，确保点路径拒绝和
`/aicardhub` 路由先匹配。人工检查现有 `^~` 或 regex location 是否会抢占
`/aicardhub`；如有冲突由 mainline 评估并调整主机配置，本包不自动修改。确认后：

```bash
nginx -t && systemctl reload nginx
```

验证 `/aicardhub/`、H5/后台深链接为 200，缺失的 `/aicardhub/assets/...` 为 404，
`/aicardhub/.git` 和 `/aicardhub/admin/x/.env` 为 404；其他站点根路径保持不变。

可选 stage：审查 `ops/nginx/aicardhub.stage.conf` 后，人工复制到独立 conf.d，
再 `nginx -t`；它只监听 `127.0.0.1:18080`，不接受公网流量。

## 7. 安装 release、迁移门禁和激活

artifact 根布局必须是 `server/`、`apps/h5/dist/`、`apps/admin/dist/`、`venv/`。
`release.sh` 会校验归档、确认 Python 3.12，复制为 root-owned 只读目录，默认不切换
current：

```bash
sudo scripts/release.sh --config /etc/aicardhub/deploy.conf \
  --artifact /secure/releases/aicardhub-<id>.tar.gz \
  --release-id <id>
```

mainline 完成数据迁移后，创建 root:root 0600 迁移门禁，内容必须匹配 release：

```text
release_id=<id>
schema_compatible=yes
alembic_revision=<approved-revision>
approved_by=<mainline-role>
```

然后激活：

```bash
sudo scripts/activate.sh --config /etc/aicardhub/deploy.conf --release-id <id>
```

激活先停止 scheduler 和 API（停止失败即中止，不改 `current`），再原子切换 `current`，
只启动 API 并通过 loopback health 后才启动 scheduler。不会反向迁移数据库，也不会
reload nginx。

任何切换失败都会先停止两个 unit，并把 `current` 保留在失败时的目标；**不会**自动
重启旧 release（其 schema 兼容性未知）。操作者必须为旧目标重新创建匹配的迁移门禁，
再显式执行 `rollback.sh`。若目标就是当前 release 但不健康，激活在门禁通过后会走
同样的停止/启动/health 流程以恢复它。

## 8. 回滚

```bash
sudo scripts/rollback.sh --config /etc/aicardhub/deploy.conf --to <previous-id>
```

目标 release 必须仍存在；迁移门禁必须指向目标，并同时提供 `schema_compatible=yes`、
有效的 `alembic_revision` 和 `approved_by`。回滚同样先停止两个 unit，API health 通过后
才启动 scheduler。失败时两个 unit 保持停止，不自动重启任何 release；修正门禁后由操作者
再次显式执行。回滚只切换代码和重启服务，不恢复数据库；schema 不兼容时由 mainline
决定向前修复。

## 9. 备份与人工恢复

将 `templates/backup.env.example` 复制为 `/etc/aicardhub/backup.env`，MySQL 凭据只放
`MYSQL_DEFAULTS_FILE`（root:root 0600）。手动备份：

```bash
sudo /opt/aicardhub/ops/backup.sh --config /etc/aicardhub/backup.env
```

备份会短暂停止 API/scheduler，生成 `database.sql`、`files.tar`（uploads、kb 含
`.git`、env）、`SHA256SUMS` 和 `MANIFEST`，归档权限 0700/0600。确认配置后可
`systemctl enable --now aicardhub-backup.timer`。

恢复只做验证并打印人工步骤，不自动执行：

```bash
sudo /opt/aicardhub/ops/restore.sh --config /etc/aicardhub/backup.env \
  --backup-dir /var/backups/aicardhub/aicardhub-backup-<timestamp>
```

`restore.sh` 先做结构校验：`SHA256SUMS` 只能列出 `database.sql`、`files.tar` 两个精确
路径；`files.tar` 用 Python `tarfile` 解析，只允许 `env` 常规文件以及 `uploads/`、
`kb/` 下的常规文件和目录，拒绝符号链接、硬链接、设备、FIFO、绝对路径、穿越路径和
重复路径，并确认三者都存在。脚本只打印人工步骤，不执行恢复。

人工步骤按输出的安全顺序执行：停止两个服务 → 恢复 MySQL → 在 `shared/` 同文件系统的
空 `mktemp` 暂存目录解包已校验归档 → 不覆盖、不 `rm -rf`，先把现有 `uploads`/`kb`
改名为 `.retained-<timestamp>` 保留，再移入暂存目录 → 单独、可选、显式地处理 `env`
并保留旧文件 → 修正所有权/标签 → 先启动 API 并检查 health，成功后才启动 scheduler。
任何一步失败都保持两个服务停止。数据库恢复不可逆，必须有独立授权和新备份。

## 10. 日志、SELinux 和验证边界

- API/scheduler 使用 journald；nginx 使用专用 access/error 日志；备份写独立日志。
  logrotate 只处理这些专用文件，不改 journald 策略。
- Enforcing 时由 mainline 按实际标签确认；窄范围 fcontext 应覆盖
  `releases/[^/]+/apps/h5/dist`、`.../admin/dist` 和 `shared/uploads`，loopback
  18000 需标记为 `http_port_t`。先检查，避免重复添加。
- 本目录本地验证：`bash scripts/verify-local.sh`。该验证不是 `nginx -t` 或
  `systemd-analyze verify` 的替代。
- 本次未执行远程操作、真实 nginx/systemd、SSE、MySQL 备份/恢复或生产验收；
  未运行依赖数据库和 secret 的 `scripts/check.sh`。不要据此宣称已完成完整验证；
  本地输出只以 `evidence/final-validation.txt` 的实际内容为准。
