#!/usr/bin/env bash
# aicardhub-native: atomic current-symlink switch, health gate and rollback.
set -Eeuo pipefail
IFS=$'\n\t'
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

usage() {
    cat >&2 <<'EOF'
Usage: activate.sh --config FILE --release-id ID [--force] [--lock-held]

Requires a root-owned 0600 migration gate written by mainline after the approved
schema migration. The gate must contain:
  release_id=<this release>
  schema_compatible=yes
  alembic_revision=<non-empty revision>
  approved_by=<name/role>
This script never runs Alembic, seeds, copies data, reloads nginx or reverses DB
changes. Both units are stopped before the switch. The API must pass its loopback
health check before the scheduler is started. On any failed switch both units are
left stopped and the current symlink is retained; the old release is NEVER
restarted automatically because its schema compatibility is unknown. To recover
an old release, the operator must create a fresh migration gate naming that
release and run rollback.sh explicitly. Release directories are retained.
EOF
}

config=""
release_id=""
force=0
lock_held=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --config) config="${2:-}"; shift 2 ;;
        --release-id) release_id="${2:-}"; shift 2 ;;
        --force) force=1; shift ;;
        --lock-held) lock_held=1; shift ;;
        --help|-h) usage; exit 0 ;;
        *) usage; die "unknown argument: $1" ;;
    esac
done
[ -n "$config" ] || { usage; die "--config is required"; }
[ -n "$release_id" ] || { usage; die "--release-id is required"; }
[[ "$release_id" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$ ]] || die "invalid release id"
load_config "$config"
require_keys RELEASES_DIR CURRENT_LINK ENV_FILE MIGRATION_GATE_FILE API_UNIT SCHEDULER_UNIT API_HOST API_PORT DEPLOY_LOCK MAINTENANCE_LOCK
render_check "$config" >/dev/null
require_root
if [ "$lock_held" -eq 0 ]; then acquire_lock "$(cfg DEPLOY_LOCK)"; fi

release_path="$(cfg RELEASES_DIR)/$release_id"
[ -d "$release_path" ] || die "release not found: $release_path"
[ ! -L "$release_path" ] || die "release must not be a symlink: $release_path"
require_private_file "$(cfg ENV_FILE)" "product environment"
require_private_file "$(cfg MIGRATION_GATE_FILE)" "migration gate"
[ -f "$release_path/RELEASE-METADATA" ] || die "release metadata missing: $release_path/RELEASE-METADATA"
[ "$(awk -F= '$1=="release_id" {print $2; exit}' "$release_path/RELEASE-METADATA")" = "$release_id" ] \
    || die "release metadata id does not match $release_id"

"$SCRIPT_DIR/preflight.sh" --config "$config" --mode activate --release-dir "$release_path"

gate_value() {
    awk -F= -v key="$1" '$1==key {sub(/^[^=]*=/, ""); print; exit}' "$(cfg MIGRATION_GATE_FILE)"
}
gate_release="$(gate_value release_id)"
gate_compatible="$(gate_value schema_compatible)"
gate_revision="$(gate_value alembic_revision)"
gate_approved="$(gate_value approved_by)"
[ "$gate_release" = "$release_id" ] || die "migration gate is for '${gate_release}', expected '$release_id'"
[ "$gate_compatible" = "yes" ] || die "migration gate does not confirm schema compatibility"
[[ "$gate_revision" =~ ^[A-Za-z0-9_]{1,64}$ ]] || die "migration gate has no valid alembic revision"
[ -n "$gate_approved" ] || die "migration gate has no approver"
log "migration gate accepted: release=$release_id revision=$gate_revision"

current_link="$(cfg CURRENT_LINK)"
old_target=""
if [ -L "$current_link" ]; then
    old_target="$(readlink -f "$current_link")"
    case "$old_target" in
        "$(cfg RELEASES_DIR)"/*) ;;
        *) die "current symlink points outside RELEASES_DIR: $old_target" ;;
    esac
fi

health_url="http://$(cfg API_HOST):$(cfg API_PORT)/health"
api_unit="$(cfg API_UNIT)"
scheduler_unit="$(cfg SCHEDULER_UNIT)"

services_healthy() {
    service_active "$api_unit" && service_active "$scheduler_unit" && health_check "$health_url" 1 1
}

if [ -L "$current_link" ] && [ "$(readlink -f "$current_link")" = "$release_path" ] && [ "$force" -eq 0 ]; then
    if services_healthy; then
        log "release $release_id is already current and healthy"
        exit 0
    fi
    log "release $release_id is current but unhealthy; restarting after the gate"
fi

fail_activation() {
    local reason="$1"
    warn "activation failed: $reason"
    warn "stopping both units; no previous release is restarted automatically"
    systemctl stop "$scheduler_unit" 2>/dev/null || true
    systemctl stop "$api_unit" 2>/dev/null || true
    warn "both units are left stopped; current symlink retained at $current_link"
    if [ -n "$old_target" ]; then
        warn "old release retained at $old_target"
        warn "to use it again, create a fresh migration gate naming its release_id and run rollback.sh --to <its-id>; do not force"
    fi
    exit 1
}

log "stopping scheduler and API before the switch"
systemctl stop "$scheduler_unit" || fail_activation "cannot stop the scheduler unit"
systemctl stop "$api_unit" || fail_activation "cannot stop the API unit"

log "switching current -> $release_path"
atomic_symlink "$release_path" "$current_link" || fail_activation "cannot update current symlink"
systemctl enable "$api_unit" "$scheduler_unit" >/dev/null 2>&1 || fail_activation "cannot enable units"
log "starting API for health verification"
systemctl restart "$api_unit" || fail_activation "API failed to restart"
health_check "$health_url" 30 1 || fail_activation "API health check did not pass within 30s"
log "API health check passed; starting the scheduler"
systemctl restart "$scheduler_unit" || fail_activation "scheduler failed to restart"
sleep 3
service_active "$scheduler_unit" || fail_activation "scheduler is not active"
log "activation complete: $release_id is current; database was not changed by this script"
