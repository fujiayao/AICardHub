#!/usr/bin/env bash
# aicardhub-native: read-only EL9 preflight. No package installation or service changes.
set -Eeuo pipefail
IFS=$'\n\t'
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

usage() {
    cat >&2 <<'EOF'
Usage: preflight.sh --config FILE --mode render|install|activate [options]

Options:
  --release-dir DIR   check a specific release (required for activate checks)
  --with-backup       require private backup env and MySQL defaults file
  --help              show this help

Exit status is non-zero when a prerequisite is missing. This script never
installs packages, starts services, inserts nginx includes, runs nginx -t, or
changes SELinux policy.
EOF
}

mode=""
config=""
release_dir=""
with_backup=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --config) config="${2:-}"; shift 2 ;;
        --mode) mode="${2:-}"; shift 2 ;;
        --release-dir) release_dir="${2:-}"; shift 2 ;;
        --with-backup) with_backup=1; shift ;;
        --help|-h) usage; exit 0 ;;
        *) usage; die "unknown argument: $1" ;;
    esac
done
[ -n "$config" ] || { usage; die "--config is required"; }
case "$mode" in render|install|activate) ;; *) usage; die "--mode must be render, install or activate" ;; esac
load_config "$config"
require_keys DEPLOY_ROOT SERVICE_USER SERVICE_GROUP RELEASES_DIR SHARED_DIR UPLOAD_DIR KB_DIR LOG_DIR OPS_DIR CURRENT_LINK ENV_FILE MIGRATION_GATE_FILE API_HOST API_PORT API_UNIT SCHEDULER_UNIT BACKUP_UNIT BACKUP_TIMER SITE_NAME SITE_DOMAIN NGINX_INCLUDE_FILE STAGE_CONF_FILE STAGE_LISTEN STAGE_SERVER_NAME NGINX_LOG_DIR NGINX_ACCESS_LOG NGINX_ERROR_LOG LOGROTATE_CONF_DIR SYSTEMD_UNIT_DIR BACKUP_ROOT BACKUP_ENV_FILE MYSQL_DEFAULTS_FILE DEPLOY_LOCK MAINTENANCE_LOCK PYTHON_RUNTIME
render_check "$config" >/dev/null
log "configuration valid"

if [ "$mode" = "render" ]; then
    python_bin >/dev/null || die "python3 is required for rendering"
    log "preflight render passed (no host changes)"
    exit 0
fi

require_root
[ -r /etc/os-release ] || die "/etc/os-release is missing; EL9 is required"
# /etc/os-release is a trusted system file of simple KEY=VALUE assignments.
. /etc/os-release
case "${ID:-} ${ID_LIKE:-}" in
    *ubuntu*|*debian*) die "Ubuntu/Debian is not supported; this runbook targets EL9 only" ;;
esac
case "${VERSION_ID:-}" in
    9|9.*) ;;
    *) die "EL9 is required; found VERSION_ID=${VERSION_ID:-unknown}" ;;
esac
case "${ID:-}" in
    centos|rhel|rocky|almalinux|ol) ;;
    *) case " ${ID_LIKE:-} " in *" rhel "*) ;; *) die "EL9-compatible distribution required (found ${ID:-unknown})" ;; esac ;;
esac
log "operating system: ${PRETTY_NAME:-EL9}"

required_commands=(bash systemctl nginx curl flock tar gzip sha256sum find stat getent groupadd useradd install awk sed grep head tail readlink mktemp ss date sleep dirname basename cut sort uniq)
for command in "${required_commands[@]}"; do
    need_cmd "$command"
done
need_cmd git || die "git is required at runtime by the knowledge store; install it through the approved EL9 process"
if command -v uv >/dev/null 2>&1; then
    warn "uv is present but is not used on production; the release carries a prebuilt venv"
else
    log "uv is not installed (expected; no build happens on production)"
fi
if command -v mysqldump >/dev/null 2>&1; then
    log "mysqldump present"
else
    warn "mysqldump is not installed; backups are blocked until the MySQL client is provisioned"
fi

python_runtime="$(cfg PYTHON_RUNTIME)"
[ -x "$python_runtime" ] || die "Python 3.12 runtime missing: $python_runtime (server prerequisite pending)"
"$python_runtime" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)' \
    || die "$python_runtime is not Python 3.12; the prebuilt venv requires exactly 3.12"
log "python runtime: $("$python_runtime" -c 'import sys; print(sys.version.split()[0])')"

for directory in "$(cfg NGINX_LOG_DIR)" "$(cfg LOGROTATE_CONF_DIR)" "$(cfg SYSTEMD_UNIT_DIR)"; do
    [ -d "$directory" ] || die "required directory missing: $directory"
done
[ -d "$(dirname "$(cfg DEPLOY_ROOT)")" ] || die "parent of DEPLOY_ROOT is missing: $(dirname "$(cfg DEPLOY_ROOT)")"

deploy_root="$(cfg DEPLOY_ROOT)"
if [ -L "$deploy_root" ]; then
    die "DEPLOY_ROOT must not be a symlink: $deploy_root"
fi
if [ -e "$deploy_root" ] && [ ! -d "$deploy_root" ]; then
    die "DEPLOY_ROOT exists but is not a directory: $deploy_root"
fi

check_target() {
    local path="$1"
    if [ -e "$path" ] && ! is_generated "$path"; then
        die "refusing to overwrite unmanaged file: $path"
    fi
}
check_shell_target() {
    local path="$1"
    if [ -e "$path" ] && ! is_managed_shell "$path"; then
        die "refusing to overwrite unmanaged shell file: $path"
    fi
}
check_target "$(cfg SYSTEMD_UNIT_DIR)/$(cfg API_UNIT)"
check_target "$(cfg SYSTEMD_UNIT_DIR)/$(cfg SCHEDULER_UNIT)"
check_target "$(cfg SYSTEMD_UNIT_DIR)/$(cfg BACKUP_UNIT)"
check_target "$(cfg SYSTEMD_UNIT_DIR)/$(cfg BACKUP_TIMER)"
check_target "$(cfg NGINX_INCLUDE_FILE)"
check_target "$(cfg STAGE_CONF_FILE)"
check_target "$(cfg LOGROTATE_CONF_DIR)/$(cfg SITE_NAME)"
check_shell_target "$(cfg OPS_DIR)/lib.sh"
check_shell_target "$(cfg OPS_DIR)/backup.sh"
check_shell_target "$(cfg OPS_DIR)/restore.sh"

if [ -e "$(cfg ENV_FILE)" ]; then
    require_private_file "$(cfg ENV_FILE)" "product environment"
else
    warn "product environment not installed yet: $(cfg ENV_FILE)"
fi
if [ -e "$(cfg MIGRATION_GATE_FILE)" ]; then
    require_private_file "$(cfg MIGRATION_GATE_FILE)" "migration gate"
else
    warn "migration gate not present yet: $(cfg MIGRATION_GATE_FILE)"
fi

if [ "$with_backup" -eq 1 ]; then
    require_private_file "$(cfg BACKUP_ENV_FILE)" "backup configuration"
    require_private_file "$(cfg MYSQL_DEFAULTS_FILE)" "MySQL backup defaults file"
fi

api_port="$(cfg API_PORT)"
case " $api_port " in
    " 80 "|" 443 "|" 3306 ") die "API_PORT collides with a reserved service" ;;
esac
if ss -H -ltn "sport = :$api_port" 2>/dev/null | grep -q .; then
    if service_active "$(cfg API_UNIT)"; then
        log "API port $api_port is owned by the existing AICardHub API service"
    else
        die "API port $api_port is already in use by another process"
    fi
else
    log "API port $api_port is free"
fi

available_kb="$(df -Pk "$(dirname "$deploy_root")" | awk 'NR==2 {print $4}')"
[ -n "$available_kb" ] || die "cannot determine free disk space"
[ "$available_kb" -ge 1048576 ] || die "less than 1 GiB free under $(dirname "$deploy_root")"
mem_total_kb="$(awk '/^MemTotal:/ {print $2}' /proc/meminfo)"
if [ -n "$mem_total_kb" ] && [ "$mem_total_kb" -lt 3145728 ]; then
    warn "total RAM is below 3 GiB; keep one API worker and no on-host builds"
fi
log "disk free: $((available_kb / 1024)) MiB; RAM total: $((mem_total_kb / 1024)) MiB"

if command -v getenforce >/dev/null 2>&1; then
    selinux_status="$(getenforce)"
    log "SELinux: $selinux_status"
    if [ "$selinux_status" = "Enforcing" ]; then
        command -v matchpathcon >/dev/null 2>&1 || die "policycoreutils is required for SELinux checks (matchpathcon missing)"
        command -v semanage >/dev/null 2>&1 || die "policycoreutils-python-utils is required for SELinux checks (semanage missing)"
        context_type() {
            matchpathcon -n "$1" 2>/dev/null | awk -F: '{print $3}' | tail -n 1
        }
        uploads_type="$(context_type "$(cfg UPLOAD_DIR)")"
        [ "$uploads_type" = "httpd_sys_content_t" ] || die "SELinux label for $(cfg UPLOAD_DIR) is '${uploads_type}', expected httpd_sys_content_t; apply the narrow fcontext rules in README.md"
        if [ "$mode" = "activate" ] && [ -n "$release_dir" ]; then
            h5_type="$(context_type "$release_dir/apps/h5/dist/index.html")"
            admin_type="$(context_type "$release_dir/apps/admin/dist/index.html")"
            [ "$h5_type" = "httpd_sys_content_t" ] || die "SELinux label for $release_dir/apps/h5/dist is '${h5_type}', expected httpd_sys_content_t"
            [ "$admin_type" = "httpd_sys_content_t" ] || die "SELinux label for $release_dir/apps/admin/dist is '${admin_type}', expected httpd_sys_content_t"
        fi
        if ! semanage port -l | grep -E '^http_port_t[[:space:]]+tcp' | grep -qw "$api_port"; then
            die "SELinux does not label tcp/$api_port as http_port_t; use the narrow semanage port step in README.md instead of a global boolean"
        fi
    fi
else
    warn "getenforce is unavailable; SELinux assessment must be completed by the operator"
fi

if [ "$mode" = "activate" ]; then
    [ -n "$release_dir" ] || die "--release-dir is required for activate preflight"
    [ -d "$release_dir" ] || die "release directory missing: $release_dir"
    [ -f "$release_dir/server/app/main.py" ] || die "release is missing server/app/main.py"
    [ -f "$release_dir/apps/h5/dist/index.html" ] || die "release is missing apps/h5/dist/index.html"
    [ -f "$release_dir/apps/admin/dist/index.html" ] || die "release is missing apps/admin/dist/index.html"
    [ "$(file_owner "$release_dir")" = "root:root" ] || die "release directory must be root:root"
    if find "$release_dir" \( -user "$(cfg SERVICE_USER)" -o -group "$(cfg SERVICE_GROUP)" -o -perm -g+w -o -perm -o+w \) -print -quit | grep -q .; then
        die "release code is writable by the service user/group or others"
    fi
    [ -f "$(cfg SYSTEMD_UNIT_DIR)/$(cfg API_UNIT)" ] || die "API unit is not installed"
    [ -f "$(cfg SYSTEMD_UNIT_DIR)/$(cfg SCHEDULER_UNIT)" ] || die "scheduler unit is not installed"
    require_private_file "$(cfg ENV_FILE)" "product environment"
    require_private_file "$(cfg MIGRATION_GATE_FILE)" "migration gate"
    if [ -L "$(cfg CURRENT_LINK)" ]; then
        target="$(readlink -f "$(cfg CURRENT_LINK)")"
        case "$target" in
            "$(cfg RELEASES_DIR)"/*) ;;
            *) die "current symlink points outside RELEASES_DIR: $target" ;;
        esac
    elif [ -e "$(cfg CURRENT_LINK)" ]; then
        die "CURRENT_LINK exists but is not a symlink"
    fi
fi

log "preflight $mode passed; no changes were made"
