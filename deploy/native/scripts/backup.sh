#!/usr/bin/env bash
# aicardhub-native: private MySQL + files backup with service quiescing.
set -Eeuo pipefail
IFS=$'\n\t'
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

usage() {
    cat >&2 <<'EOF'
Usage: backup.sh --config FILE

Creates one private backup directory under BACKUP_ROOT containing:
  database.sql   consistent MySQL logical dump (single transaction)
  files.tar      entire shared/uploads, shared/kb (including .git) and shared/env
  SHA256SUMS     integrity hashes
  MANIFEST       non-secret metadata
The API and scheduler are briefly stopped for a coherent DB/files snapshot and
restarted by an EXIT trap even on failure. A restart failure makes the command
exit non-zero. Completed backups are 0700/0600.
No password is accepted on the command line; MySQL credentials live only in a
root-owned 0600 defaults-extra-file. No restore is performed here.
EOF
}

config=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --config) config="${2:-}"; shift 2 ;;
        --help|-h) usage; exit 0 ;;
        *) usage; die "unknown argument: $1" ;;
    esac
done
[ -n "$config" ] || { usage; die "--config is required"; }
load_config "$config"
require_keys DEPLOY_ROOT BACKUP_ROOT BACKUP_RETENTION_DAYS BACKUP_LOG LOG_DIR LOG_GROUP MYSQL_DEFAULTS_FILE MYSQL_DATABASE MYSQL_DUMP_BIN API_HOST API_PORT SERVICE_USER SERVICE_GROUP SHARED_DIR UPLOAD_DIR KB_DIR ENV_FILE RELEASES_DIR CURRENT_LINK API_UNIT SCHEDULER_UNIT DEPLOY_LOCK MAINTENANCE_LOCK
require_root
umask 077

deploy_root="$(cfg DEPLOY_ROOT)"
backup_root="$(cfg BACKUP_ROOT)"
shared_dir="$(cfg SHARED_DIR)"
upload_dir="$(cfg UPLOAD_DIR)"
kb_dir="$(cfg KB_DIR)"
env_file="$(cfg ENV_FILE)"
log_file="$(cfg BACKUP_LOG)"
log_group="$(cfg LOG_GROUP)"
mysql_cnf="$(cfg MYSQL_DEFAULTS_FILE)"
database="$(cfg MYSQL_DATABASE)"
retention="$(cfg BACKUP_RETENTION_DAYS)"
api_unit="$(cfg API_UNIT)"
scheduler_unit="$(cfg SCHEDULER_UNIT)"
maintenance_lock="$(cfg MAINTENANCE_LOCK)"

# Validate the complete path/unit/lock relationship before creating a log,
# taking a lock, stopping a service or writing any backup output.
case "$backup_root" in
    /|""|*..*) die "unsafe BACKUP_ROOT: $backup_root" ;;
esac
case "$backup_root/" in
    "$deploy_root"/*) die "BACKUP_ROOT must be outside DEPLOY_ROOT" ;;
esac
[ "$(cfg DEPLOY_LOCK)" = "$maintenance_lock" ] || die "DEPLOY_LOCK and MAINTENANCE_LOCK must be the same common maintenance lock"
[ "$api_unit" != "$scheduler_unit" ] || die "API_UNIT and SCHEDULER_UNIT must differ"
[ "$upload_dir" = "$shared_dir/uploads" ] || die "UPLOAD_DIR must be SHARED_DIR/uploads"
[ "$kb_dir" = "$shared_dir/kb" ] || die "KB_DIR must be SHARED_DIR/kb"
[ "$env_file" = "$shared_dir/env" ] || die "ENV_FILE must be SHARED_DIR/env"
case "$log_file/" in
    "$(cfg LOG_DIR)"/*) ;;
    *) die "BACKUP_LOG must be under LOG_DIR" ;;
esac
[ -d "$(dirname "$backup_root")" ] || die "parent of BACKUP_ROOT is missing: $(dirname "$backup_root")"
[ -d "$(dirname "$log_file")" ] || die "backup log directory is missing: $(dirname "$log_file")"
getent group "$log_group" >/dev/null || die "log group does not exist: $log_group"
[ "$retention" -ge 1 ] && [ "$retention" -le 365 ] || die "BACKUP_RETENTION_DAYS out of range"
require_private_file "$env_file" "product environment"
require_private_file "$mysql_cnf" "MySQL backup defaults file"
for directory in "$shared_dir" "$upload_dir" "$kb_dir"; do
    [ -d "$directory" ] || die "shared directory missing: $directory"
    [ ! -L "$directory" ] || die "shared directory must not be a symlink: $directory"
done

mysql_dump="$(cfg MYSQL_DUMP_BIN)"
case "$mysql_dump" in
    */*) [ -x "$mysql_dump" ] || die "MySQL dump binary not executable: $mysql_dump" ;;
    *) need_cmd "$mysql_dump" || die "MySQL dump command not found: $mysql_dump" ;;
esac

need_cmd flock
need_cmd tar
need_cmd sha256sum
need_cmd find
need_cmd stat
need_cmd install
need_cmd systemctl
need_cmd awk
need_cmd sed
need_cmd grep
need_cmd readlink
need_cmd mktemp
need_cmd sort
need_cmd tail
need_cmd date

if [ -L "$backup_root" ]; then
    die "BACKUP_ROOT must not be a symlink: $backup_root"
fi
if [ -e "$backup_root" ]; then
    [ -d "$backup_root" ] || die "BACKUP_ROOT is not a directory"
    [ "$(file_owner "$backup_root")" = "root:root" ] || die "BACKUP_ROOT must be root:root"
else
    install -d -o root -g root -m 0700 "$backup_root"
fi
if [ -e "$log_file" ]; then
    [ -f "$log_file" ] && [ ! -L "$log_file" ] || die "backup log must be a regular file"
    [ "$(stat -c '%U' "$log_file")" = "root" ] || die "backup log must be owned by root"
else
    install -m 0640 -o root -g "$log_group" /dev/null "$log_file"
fi

acquire_lock "$maintenance_lock"

blog() {
    local line
    line="[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*"
    printf '%s\n' "$line" >&2
    printf '%s\n' "$line" >> "$log_file"
}

stopped_api=0
stopped_scheduler=0
services_restored=0
tmp=""

restore_services() {
    local rc=0
    [ "$services_restored" -eq 0 ] || return 0
    services_restored=1
    if [ "$stopped_api" -eq 1 ]; then
        if systemctl start "$api_unit"; then
            blog "API restarted"
        else
            blog "ERROR: API could not be restarted; operator attention required"
            rc=1
        fi
    fi
    if [ "$stopped_scheduler" -eq 1 ]; then
        if systemctl start "$scheduler_unit"; then
            blog "scheduler restarted"
        else
            blog "ERROR: scheduler could not be restarted; operator attention required"
            rc=1
        fi
    fi
    return "$rc"
}

cleanup_partial() {
    if [ -n "${tmp:-}" ] && [ -d "$tmp" ]; then
        case "$tmp" in
            "$backup_root"/.partial-aicardhub-backup-*) rm -rf -- "$tmp" ;;
            *) blog "refusing to remove unexpected partial path: $tmp" ;;
        esac
    fi
}

on_exit() {
    local rc=$?
    trap - EXIT
    if ! restore_services; then
        blog "ERROR: service restart failed during backup exit; command will be non-zero"
        [ "$rc" -ne 0 ] || rc=1
    fi
    cleanup_partial
    exit "$rc"
}
trap on_exit EXIT

blog "backup starting"
if service_active "$scheduler_unit"; then
    stopped_scheduler=1
    systemctl stop "$scheduler_unit" || die "failed to stop scheduler"
fi
if service_active "$api_unit"; then
    stopped_api=1
    systemctl stop "$api_unit" || die "failed to stop API"
fi
if service_active "$api_unit" || service_active "$scheduler_unit"; then
    die "AICardHub services are still active; refusing an incoherent snapshot"
fi

backup_id="aicardhub-backup-$(date -u '+%Y%m%dT%H%M%SZ')"
final="$backup_root/$backup_id"
[ ! -e "$final" ] || die "backup already exists: $final"
tmp="$(mktemp -d "$backup_root/.partial-$backup_id.XXXXXX")"
chmod 0700 "$tmp"

dump_args=(
    "--defaults-extra-file=$mysql_cnf"
    --single-transaction
    --quick
    --routines
    --events
    --triggers
    --set-gtid-purged=OFF
    --no-tablespaces
    --default-character-set=utf8mb4
    --databases "$database"
)
if ! "$mysql_dump" "${dump_args[@]}" >"$tmp/database.sql" 2>"$tmp/mysqldump.stderr"; then
    blog "mysqldump failed; its stderr is not echoed because the client config may contain credentials"
    exit 1
fi
[ -s "$tmp/database.sql" ] || die "MySQL dump is empty"
tail -n 20 "$tmp/database.sql" | grep -q '^-- Dump completed' || die "MySQL dump lacks completion marker"
rm -f -- "$tmp/mysqldump.stderr"
chmod 0600 "$tmp/database.sql"
blog "MySQL logical dump completed"

tar -C "$shared_dir" -cpf "$tmp/files.tar" uploads kb env
[ -s "$tmp/files.tar" ] || die "files archive is empty"
tar -tf "$tmp/files.tar" >"$tmp/files.list"
grep -qx 'env' "$tmp/files.list" || die "files archive is missing env"
grep -q '^kb/' "$tmp/files.list" || die "files archive is missing kb"
grep -q '^uploads/' "$tmp/files.list" || die "files archive is missing uploads"
chmod 0600 "$tmp/files.tar" "$tmp/files.list"
blog "uploads, entire kb including .git, and protected env archived"

(
    cd "$tmp"
    sha256sum database.sql files.tar >SHA256SUMS
    chmod 0600 SHA256SUMS
)
release_id="none"
if [ -L "$(cfg CURRENT_LINK)" ]; then
    release_id="$(basename "$(readlink -f "$(cfg CURRENT_LINK)")")"
fi
cat >"$tmp/MANIFEST" <<EOF
backup_id=$backup_id
created_at=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
release_id=$release_id
database=$database
retention_days=$retention
contents=database.sql,files.tar
files_scope=uploads,kb(including .git),env
database_bytes=$(stat -c '%s' "$tmp/database.sql")
files_bytes=$(stat -c '%s' "$tmp/files.tar")
EOF
chmod 0600 "$tmp/MANIFEST"
chown -R root:root "$tmp"

mv "$tmp" "$final"
tmp=""
blog "backup complete: $final"

if ! restore_services; then
    blog "ERROR: one or more AICardHub services failed to restart after backup"
    exit 1
fi
if [ "$stopped_api" -eq 1 ] && ! service_active "$api_unit"; then
    blog "ERROR: API is not active after backup"
    exit 1
fi
if [ "$stopped_scheduler" -eq 1 ] && ! service_active "$scheduler_unit"; then
    blog "ERROR: scheduler is not active after backup"
    exit 1
fi
if [ "$stopped_api" -eq 1 ] && ! health_check "http://$(cfg API_HOST):$(cfg API_PORT)/health" 10 1; then
    blog "WARNING: API health check after backup did not pass; inspect journalctl"
fi

while IFS= read -r old; do
    [ -d "$old" ] && [ ! -L "$old" ] || continue
    [ "$(file_owner "$old")" = "root:root" ] || { blog "retention skipped non-root backup: $old"; continue; }
    [ -f "$old/MANIFEST" ] && [ -f "$old/SHA256SUMS" ] || { blog "retention skipped unverified backup: $old"; continue; }
    grep -q '^backup_id=aicardhub-backup-' "$old/MANIFEST" || { blog "retention skipped backup without own manifest: $old"; continue; }
    if (cd "$old" && sha256sum -c SHA256SUMS >/dev/null 2>&1); then
        rm -rf -- "$old"
    else
        blog "retention skipped backup with failed checksum: $old"
    fi
done < <(find "$backup_root" -mindepth 1 -maxdepth 1 -type d -name 'aicardhub-backup-*' -mtime +"$retention" -print)
while IFS= read -r old; do
    [ -d "$old" ] && [ ! -L "$old" ] || continue
    case "$old" in
        "$backup_root"/.partial-aicardhub-backup-*) rm -rf -- "$old" ;;
    esac
done < <(find "$backup_root" -mindepth 1 -maxdepth 1 -type d -name '.partial-aicardhub-backup-*' -mtime +2 -print)
blog "backup finished"
