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

Switches current to a retained release and requires the same gate as activation:
release_id, schema_compatible=yes, a valid alembic_revision and approved_by.
Both units are stopped before the switch; the target API must pass its loopback
health check before the scheduler starts. On failure both units are left stopped
and no release is restarted automatically; the operator must fix the gate and
rerun explicitly. Rollback never reverses database migrations or restores data.
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
[ -f "$target/RELEASE-METADATA" ] || die "release metadata missing: $target/RELEASE-METADATA"
[ "$(awk -F= '$1=="release_id" {print $2; exit}' "$target/RELEASE-METADATA")" = "$target_id" ] \
    || die "release metadata id does not match $target_id"
"$SCRIPT_DIR/preflight.sh" --config "$config" --mode activate --release-dir "$target"

gate_value() {
    awk -F= -v key="$1" '$1==key {sub(/^[^=]*=/, ""); print; exit}' "$(cfg MIGRATION_GATE_FILE)"
}
gate_release="$(gate_value release_id)"
gate_compatible="$(gate_value schema_compatible)"
gate_revision="$(gate_value alembic_revision)"
gate_approved="$(gate_value approved_by)"
[ "$gate_release" = "$target_id" ] || die "migration gate does not name target $target_id"
[ "$gate_compatible" = "yes" ] || die "migration gate does not confirm schema compatibility"
[[ "$gate_revision" =~ ^[A-Za-z0-9_]{1,64}$ ]] || die "migration gate has no valid alembic revision"
[ -n "$gate_approved" ] || die "migration gate has no approver"

current_link="$(cfg CURRENT_LINK)"
old_target=""
if [ -L "$current_link" ]; then old_target="$(readlink -f "$current_link")"; fi

api_unit="$(cfg API_UNIT)"
scheduler_unit="$(cfg SCHEDULER_UNIT)"
health_url="http://$(cfg API_HOST):$(cfg API_PORT)/health"

if [ "$old_target" = "$target" ] && service_active "$api_unit" \
    && service_active "$scheduler_unit" && health_check "$health_url" 1 1; then
    log "target release is already current and healthy"
    exit 0
fi

rollback_failed() {
    local reason="$1"
    warn "rollback failed: $reason"
    warn "stopping both units; no release is restarted automatically"
    systemctl stop "$scheduler_unit" 2>/dev/null || true
    systemctl stop "$api_unit" 2>/dev/null || true
    warn "both units are left stopped; current symlink retained at $current_link"
    warn "fix the migration gate for the intended target and rerun rollback.sh explicitly; do not force"
    exit 1
}

log "stopping scheduler and API before the switch"
systemctl stop "$scheduler_unit" || rollback_failed "cannot stop the scheduler unit"
systemctl stop "$api_unit" || rollback_failed "cannot stop the API unit"

log "switching current -> $target"
atomic_symlink "$target" "$current_link" || rollback_failed "cannot update current symlink"
systemctl enable "$api_unit" "$scheduler_unit" >/dev/null 2>&1 || rollback_failed "cannot enable units"
log "starting API for health verification"
systemctl restart "$api_unit" || rollback_failed "API failed to restart"
health_check "$health_url" 30 1 || rollback_failed "API health check did not pass within 30s"
log "API health check passed; starting the scheduler"
systemctl restart "$scheduler_unit" || rollback_failed "scheduler failed to restart"
sleep 3
service_active "$scheduler_unit" || rollback_failed "scheduler is not active"
log "rollback complete: $target_id is current; database was not changed"
