#!/usr/bin/env bash
# aicardhub-native: opt-in installer for units, prefix locations, logrotate and ops scripts.
set -Eeuo pipefail
IFS=$'\n\t'
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

usage() {
    cat >&2 <<'EOF'
Usage: install.sh --config FILE [options]

Options:
  --env-file PATH          install the product env only if absent (root:root 0600)
  --render                 render and copy the prefix locations include (default)
  --install-units          install API and scheduler systemd units
  --install-logrotate      install the dedicated logrotate file
  --install-backup-timer   install (but do not enable) backup service and timer
  --help                   show this help

This installer renders the nginx locations include and the optional loopback
stage wrapper into app-owned paths under OPS_DIR/nginx only. It NEVER inserts
into an existing server block, never edits nginx.conf/conf.d, never runs nginx -t
and never reloads nginx. Mainline chooses the insertion point inside the existing
TLS server, runs nginx -t, then reloads. It does not start services, enable
timers, run migrations, seed data, copy data or change existing vhosts.
EOF
}

config=""
env_source=""
render=1
install_units=0
install_logrotate=0
install_backup_timer=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --config) config="${2:-}"; shift 2 ;;
        --env-file) env_source="${2:-}"; shift 2 ;;
        --render) render=1; shift ;;
        --install-units) install_units=1; shift ;;
        --install-logrotate) install_logrotate=1; shift ;;
        --install-backup-timer) install_backup_timer=1; shift ;;
        --help|-h) usage; exit 0 ;;
        *) usage; die "unknown argument: $1" ;;
    esac
done
[ -n "$config" ] || { usage; die "--config is required"; }
load_config "$config"
require_keys DEPLOY_ROOT SERVICE_USER SERVICE_GROUP RELEASES_DIR SHARED_DIR UPLOAD_DIR KB_DIR LOG_DIR OPS_DIR CURRENT_LINK ENV_FILE API_UNIT SCHEDULER_UNIT BACKUP_UNIT BACKUP_TIMER SITE_NAME NGINX_INCLUDE_FILE STAGE_CONF_FILE LOGROTATE_CONF_DIR SYSTEMD_UNIT_DIR BACKUP_ENV_FILE MYSQL_DEFAULTS_FILE DEPLOY_LOCK MAINTENANCE_LOCK
render_check "$config" >/dev/null
require_root
acquire_lock "$(cfg DEPLOY_LOCK)"

"$SCRIPT_DIR/preflight.sh" --config "$config" --mode install

render_dir="$(mktemp -d)"
cleanup() {
    if [ -n "${render_dir:-}" ] && [ -d "$render_dir" ]; then
        rm -rf -- "$render_dir"
    fi
}
trap cleanup EXIT
py="$(config_python)" || die "python3/python is required for rendering"
"$py" "$SCRIPT_DIR/render.py" --config "$config" --out "$render_dir" --production >/dev/null
log "rendered production configuration"

"$SCRIPT_DIR/bootstrap.sh" --config "$config" --apply --lock-held

ensure_private_env() {
    local source="$1" target="${2:-$(cfg ENV_FILE)}"
    [ -f "$source" ] || die "env file not found: $source"
    [ ! -L "$source" ] || die "env source must not be a symlink: $source"
    if [ -e "$target" ]; then
        require_private_file "$target" "product environment"
        warn "existing product environment kept unchanged: $target"
    else
        install -m 0600 -o root -g root "$source" "$target"
        log "installed product environment: $target"
    fi
}
if [ -n "$env_source" ]; then
    ensure_private_env "$env_source"
fi
if [ -e "$(cfg ENV_FILE)" ]; then
    require_private_file "$(cfg ENV_FILE)" "product environment"
else
    warn "product environment is still missing: $(cfg ENV_FILE); activation will be blocked"
fi

ops_dir="$(cfg OPS_DIR)"
install_managed_shell "$SCRIPT_DIR/lib.sh" "$ops_dir/lib.sh" 0644
install_managed_shell "$SCRIPT_DIR/backup.sh" "$ops_dir/backup.sh" 0755
install_managed_shell "$SCRIPT_DIR/restore.sh" "$ops_dir/restore.sh" 0755
log "installed ops scripts under $ops_dir"

if [ "$render" -eq 1 ]; then
    install_generated "$render_dir/aicardhub.locations.conf" "$(cfg NGINX_INCLUDE_FILE)" 0644
    install_generated "$render_dir/aicardhub.stage.conf" "$(cfg STAGE_CONF_FILE)" 0644
    log "rendered prefix locations and optional stage wrapper under $(dirname "$(cfg NGINX_INCLUDE_FILE)")"
fi

if [ "$install_units" -eq 1 ]; then
    install_generated "$render_dir/$(cfg API_UNIT)" "$(cfg SYSTEMD_UNIT_DIR)/$(cfg API_UNIT)" 0644
    install_generated "$render_dir/$(cfg SCHEDULER_UNIT)" "$(cfg SYSTEMD_UNIT_DIR)/$(cfg SCHEDULER_UNIT)" 0644
    systemctl daemon-reload
    log "installed API/scheduler units; they are not enabled or started"
fi

if [ "$install_logrotate" -eq 1 ]; then
    install_generated "$render_dir/$(cfg SITE_NAME).logrotate" "$(cfg LOGROTATE_CONF_DIR)/$(cfg SITE_NAME)" 0644
    log "installed dedicated logrotate file; journald policy was not changed"
fi

if [ "$install_backup_timer" -eq 1 ]; then
    require_private_file "$(cfg BACKUP_ENV_FILE)" "backup configuration"
    require_private_file "$(cfg MYSQL_DEFAULTS_FILE)" "MySQL backup defaults file"
    install_generated "$render_dir/$(cfg BACKUP_UNIT)" "$(cfg SYSTEMD_UNIT_DIR)/$(cfg BACKUP_UNIT)" 0644
    install_generated "$render_dir/$(cfg BACKUP_TIMER)" "$(cfg SYSTEMD_UNIT_DIR)/$(cfg BACKUP_TIMER)" 0644
    systemctl daemon-reload
    log "installed backup service/timer; the timer is NOT enabled"
fi

log "install complete; no application service was started, no nginx test/reload was run and no database action was taken"
cat >&2 <<EOF
Next steps (mainline/operator):
  1. Ensure $(cfg ENV_FILE) is populated out-of-band with root:root 0600.
  2. Review $(cfg NGINX_INCLUDE_FILE) and insert ONLY inside the existing TLS
     server for haiwex.com:
         include $(cfg NGINX_INCLUDE_FILE);
     Do not put this locations file directly under conf.d: conf.d is http context.
  3. Run: nginx -t && systemctl reload nginx
  4. OPTIONAL staging: review $(cfg STAGE_CONF_FILE), copy it to a separate
     conf.d file only after approval, then run nginx -t. It listens only on
     127.0.0.1:18080.
  5. Mainline runs the approved migration gate and writes $(cfg MIGRATION_GATE_FILE).
  6. Install a prebuilt release with release.sh, then run activate.sh.
EOF
