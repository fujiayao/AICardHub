#!/usr/bin/env bash
# aicardhub-native: idempotent service account and private directory bootstrap.
set -Eeuo pipefail
IFS=$'\n\t'
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

usage() {
    cat >&2 <<'EOF'
Usage: bootstrap.sh --config FILE [--apply]

Creates the dedicated aicardhub system user/group and the native layout:
  /opt/aicardhub/{releases,shared/{uploads,kb},logs,ops}
  /var/backups/aicardhub
It never recursively chowns existing directories, never overwrites the live
environment file, and never creates the current symlink (activation does that).
Without --apply it only prints the planned actions.
EOF
}

applied=0
lock_held=0
config=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --config) config="${2:-}"; shift 2 ;;
        --apply) applied=1; shift ;;
        --lock-held) lock_held=1; shift ;;
        --help|-h) usage; exit 0 ;;
        *) usage; die "unknown argument: $1" ;;
    esac
done
[ -n "$config" ] || { usage; die "--config is required"; }
load_config "$config"
require_keys DEPLOY_ROOT SERVICE_USER SERVICE_GROUP RELEASES_DIR SHARED_DIR UPLOAD_DIR KB_DIR LOG_DIR OPS_DIR CURRENT_LINK ENV_FILE MIGRATION_GATE_FILE BACKUP_ROOT BACKUP_ENV_FILE MYSQL_DEFAULTS_FILE
[ "$(cfg SERVICE_USER)" = "aicardhub" ] || die "SERVICE_USER must be aicardhub"
[ "$(cfg SERVICE_GROUP)" = "aicardhub" ] || die "SERVICE_GROUP must be aicardhub"
render_check "$config" >/dev/null

deploy_root="$(cfg DEPLOY_ROOT)"
service_user="$(cfg SERVICE_USER)"
service_group="$(cfg SERVICE_GROUP)"
releases_dir="$(cfg RELEASES_DIR)"
shared_dir="$(cfg SHARED_DIR)"
upload_dir="$(cfg UPLOAD_DIR)"
kb_dir="$(cfg KB_DIR)"
log_dir="$(cfg LOG_DIR)"
ops_dir="$(cfg OPS_DIR)"
current_link="$(cfg CURRENT_LINK)"
env_file="$(cfg ENV_FILE)"
gate_file="$(cfg MIGRATION_GATE_FILE)"
backup_root="$(cfg BACKUP_ROOT)"
backup_env="$(cfg BACKUP_ENV_FILE)"
mysql_cnf="$(cfg MYSQL_DEFAULTS_FILE)"

plan() {
    printf 'plan: group %s, user %s (system, nologin)\n' "$service_group" "$service_user"
    printf 'plan: %s root:root 0755\n' "$deploy_root"
    printf 'plan: %s root:root 0755\n' "$releases_dir"
    printf 'plan: %s root:root 0755\n' "$shared_dir"
    printf 'plan: %s root:root 0755\n' "$ops_dir"
    printf 'plan: %s root:root 0755\n' "$log_dir"
    printf 'plan: %s %s:%s 0755\n' "$upload_dir" "$service_user" "$service_group"
    printf 'plan: %s %s:%s 0700 (private knowledge and Git history)\n' "$kb_dir" "$service_user" "$service_group"
    printf 'plan: %s root:root 0700 (private backups)\n' "$backup_root"
    printf 'plan: protect %s and %s as root:root 0600 when present\n' "$env_file" "$gate_file"
    printf 'plan: current symlink is created only by activate.sh\n'
}

ensure_group() {
    local group="$1"
    if getent group "$group" >/dev/null; then
        [ "$(getent group "$group" | cut -d: -f1)" = "$group" ] || die "group lookup mismatch"
        [ "$(getent group "$group" | cut -d: -f3)" -lt 1000 ] || die "existing $group is not a system group; refusing to adopt it"
        log "group exists: $group"
    else
        groupadd --system "$group"
        log "created group: $group"
    fi
}

ensure_user() {
    local user="$1" group="$2" home="$3" uid primary shell
    if getent passwd "$user" >/dev/null; then
        uid="$(getent passwd "$user" | cut -d: -f3)"
        home="$(getent passwd "$user" | cut -d: -f6)"
        shell="$(getent passwd "$user" | cut -d: -f7)"
        primary="$(id -gn "$user")"
        [ "$uid" -lt 1000 ] || die "existing $user is not a system account; refusing to adopt it"
        [ "$primary" = "$group" ] || die "existing $user has primary group $primary, expected $group"
        [ "$home" = "$(cfg DEPLOY_ROOT)" ] || die "existing $user home is $home, expected $(cfg DEPLOY_ROOT)"
        case "$shell" in
            */nologin|*/false) ;;
            *) die "existing $user has interactive shell $shell; refusing to adopt it" ;;
        esac
        log "service user exists and is system/nologin: $user"
    else
        useradd --system --gid "$group" --home-dir "$home" --shell /sbin/nologin \
            --comment "AICardHub service" "$user"
        log "created service user: $user"
    fi
}

ensure_dir() {
    local path="$1" owner="$2" group="$3" mode="$4" actual
    [ -n "$path" ] || die "empty directory path"
    [ ! -L "$path" ] || die "managed directory must not be a symlink: $path"
    if [ -e "$path" ]; then
        [ -d "$path" ] || die "path exists but is not a directory: $path"
        actual="$(file_owner "$path")"
        [ "$actual" = "$owner:$group" ] || die "refusing to adopt $path owned by $actual"
        chmod "$mode" "$path"
        log "directory exists: $path ($actual $mode)"
    else
        install -d -o "$owner" -g "$group" -m "$mode" "$path"
        log "created directory: $path"
    fi
}

if [ "$applied" -eq 0 ]; then
    plan
    printf 'dry run only; pass --apply to create the account and directories\n' >&2
    exit 0
fi

require_root
if [ "$lock_held" -eq 0 ]; then acquire_lock "$(cfg DEPLOY_LOCK)"; fi
ensure_group "$service_group"
ensure_user "$service_user" "$service_group" "$deploy_root"

if [ -e "$deploy_root" ]; then
    [ -d "$deploy_root" ] && [ ! -L "$deploy_root" ] || die "DEPLOY_ROOT must be a real directory"
    if [ ! -f "$deploy_root/.aicardhub-managed" ] && [ -n "$(find "$deploy_root" -mindepth 1 -maxdepth 1 -print -quit)" ]; then
        die "refusing to adopt non-empty unmanaged DEPLOY_ROOT: $deploy_root"
    fi
fi
ensure_dir "$deploy_root" root root 0755
if [ ! -f "$deploy_root/.aicardhub-managed" ]; then
    printf 'managed-by=aicardhub-native\n' >"$deploy_root/.aicardhub-managed"
    chown root:root "$deploy_root/.aicardhub-managed"
    chmod 0644 "$deploy_root/.aicardhub-managed"
fi
ensure_dir "$releases_dir" root root 0755
ensure_dir "$shared_dir" root root 0755
ensure_dir "$log_dir" root root 0750
ensure_dir "$ops_dir" root root 0755
ensure_dir "$upload_dir" "$service_user" "$service_group" 0755
ensure_dir "$kb_dir" "$service_user" "$service_group" 0700
if [ -e "$backup_root" ] && [ ! -f "$backup_root/.aicardhub-managed" ] && [ -n "$(find "$backup_root" -mindepth 1 -maxdepth 1 -print -quit)" ]; then
    die "refusing to adopt non-empty unmanaged BACKUP_ROOT: $backup_root"
fi
ensure_dir "$backup_root" root root 0700
if [ ! -f "$backup_root/.aicardhub-managed" ]; then
    printf 'managed-by=aicardhub-native\n' >"$backup_root/.aicardhub-managed"
    chown root:root "$backup_root/.aicardhub-managed"
    chmod 0644 "$backup_root/.aicardhub-managed"
fi
ensure_dir "$(dirname "$backup_env")" root root 0700
ensure_dir "$(dirname "$mysql_cnf")" root root 0700

[ ! -L "$current_link" ] || log "current symlink already exists: $(readlink -f "$current_link")"
if [ -e "$current_link" ] && [ ! -L "$current_link" ]; then
    die "CURRENT_LINK exists but is not a symlink: $current_link"
fi
if [ -e "$env_file" ]; then
    require_private_file "$env_file" "product environment"
else
    warn "product environment is not installed yet: $env_file"
fi
if [ -e "$gate_file" ]; then
    require_private_file "$gate_file" "migration gate"
fi
log "bootstrap complete"
