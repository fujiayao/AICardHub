#!/usr/bin/env bash
# aicardhub-native: switch to a retained release with the same health gate rules.
set -Eeuo pipefail
IFS=$'\n\t'
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

usage() {
    cat >&2 <<'EOF'
Usage: rollback.sh --config FILE --to RELEASE-ID [--lock-held]

Switches current to a retained release, restarts API/scheduler and requires the
same health/scheduler checks as activation. The migration gate must name the
target release and confirm that the current database schema is compatible with
it. Rollback never reverses database migrations or restores data.
EOF
}

config=""
target_id=""
lock_held=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --config) config="${2:-}"; shift 2 ;;
        --to) target_id="${2:-}"; shift 2 ;;
        --lock-held) lock_held=1; shift ;;
        --help|-h) usage; exit 0 ;;
        *) usage; die "unknown argument: $1" ;;
    esac
done
[ -n "$config" ] || { usage; die "--config is required"; }
[ -n "$target_id" ] || { usage; die "--to is required"; }
[[ "$target_id" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$ ]] || die "invalid release id"
load_config "$config"
require_keys RELEASES_DIR CURRENT_LINK ENV_FILE MIGRATION_GATE_FILE API_UNIT SCHEDULER_UNIT API_HOST API_PORT DEPLOY_LOCK MAINTENANCE_LOCK
render_check "$config" >/dev/null
require_root
if [ "$lock_held" -eq 0 ]; then acquire_lock "$(cfg DEPLOY_LOCK)"; fi

target="$(cfg RELEASES_DIR)/$target_id"
[ -d "$target" ] || die "target release not found: $target"
[ ! -L "$target" ] || die "target release must not be a symlink: $target"
require_private_file "$(cfg ENV_FILE)" "product environment"
require_private_file "$(cfg MIGRATION_GATE_FILE)" "migration gate"
"$SCRIPT_DIR/preflight.sh" --config "$config" --mode activate --release-dir "$target"

gate_value() {
    awk -F= -v key="$1" '$1==key {sub(/^[^=]*=/, ""); print; exit}' "$(cfg MIGRATION_GATE_FILE)"
}
[ "$(gate_value release_id)" = "$target_id" ] || die "migration gate does not name target $target_id"
[ "$(gate_value schema_compatible)" = "yes" ] || die "migration gate does not confirm schema compatibility"
[ -n "$(gate_value approved_by)" ] || die "migration gate has no approver"

current_link="$(cfg CURRENT_LINK)"
old_target=""
if [ -L "$current_link" ]; then old_target="$(readlink -f "$current_link")"; fi
if [ "$old_target" = "$target" ]; then
    log "target release is already current"
    exit 0
fi

api_unit="$(cfg API_UNIT)"
scheduler_unit="$(cfg SCHEDULER_UNIT)"
health_url="http://$(cfg API_HOST):$(cfg API_PORT)/health"

rollback_failed() {
    warn "rollback target failed health checks"
    if [ -n "$old_target" ]; then
        atomic_symlink "$old_target" "$current_link" || true
        systemctl restart "$api_unit" || true
        systemctl restart "$scheduler_unit" || true
        if health_check "$health_url" 20 1; then
            warn "previous current release is serving health checks again"
        else
            warn "previous release is unhealthy; operator attention required"
        fi
    fi
    exit 1
}

log "switching current -> $target"
atomic_symlink "$target" "$current_link" || rollback_failed
systemctl enable "$api_unit" "$scheduler_unit" >/dev/null 2>&1 || rollback_failed
systemctl stop "$scheduler_unit" 2>/dev/null || true
systemctl restart "$api_unit" || rollback_failed
systemctl restart "$scheduler_unit" || rollback_failed
health_check "$health_url" 30 1 || rollback_failed
sleep 3
service_active "$scheduler_unit" || rollback_failed
log "rollback complete: $target_id is current; database was not changed"
