#!/usr/bin/env bash
# aicardhub-native: verify a private backup and print the manual restore procedure.
# This script intentionally does not apply a restore or touch MySQL/data files.
set -Eeuo pipefail
IFS=$'\n\t'
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

usage() {
    cat >&2 <<'EOF'
Usage: restore.sh --config FILE --backup-dir DIR

Verifies MANIFEST, SHA256SUMS, database.sql completion marker and archive entry
names, then prints the manual restore steps. It does not stop services, run mysql,
extract files, overwrite env or change SELinux labels. Restore is a mainline/
operator operation with its own authorization.
EOF
}

config=""
backup_dir=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --config) config="${2:-}"; shift 2 ;;
        --backup-dir) backup_dir="${2:-}"; shift 2 ;;
        --help|-h) usage; exit 0 ;;
        *) usage; die "unknown argument: $1" ;;
    esac
done
[ -n "$config" ] || { usage; die "--config is required"; }
[ -n "$backup_dir" ] || { usage; die "--backup-dir is required"; }
load_config "$config"
require_keys BACKUP_ROOT MYSQL_DEFAULTS_FILE MYSQL_DATABASE SHARED_DIR UPLOAD_DIR KB_DIR ENV_FILE SERVICE_USER SERVICE_GROUP API_UNIT SCHEDULER_UNIT API_HOST API_PORT MYSQL_DUMP_BIN
require_root

backup_root="$(cfg BACKUP_ROOT)"
case "$backup_dir/" in
    "$backup_root"/aicardhub-backup-*) ;;
    *) die "backup directory must be a direct child of BACKUP_ROOT with an aicardhub-backup-* name" ;;
esac
[ -d "$backup_dir" ] || die "backup directory missing: $backup_dir"
[ ! -L "$backup_dir" ] || die "backup directory must not be a symlink"
[ "$(file_owner "$backup_dir")" = "root:root" ] || die "backup directory must be root:root"
[ "$(file_mode "$backup_dir")" = "700" ] || die "backup directory must be mode 0700"

for file in MANIFEST SHA256SUMS database.sql files.tar; do
    [ -f "$backup_dir/$file" ] || die "backup is missing $file"
    [ ! -L "$backup_dir/$file" ] || die "backup file must not be a symlink: $file"
    [ "$(stat -c '%U' "$backup_dir/$file")" = "root" ] || die "backup file must be owned by root: $file"
done
for file in database.sql files.tar; do
    [ "$(file_mode "$backup_dir/$file")" = "600" ] || die "backup file must be mode 0600: $file"
done

(
    cd "$backup_dir"
    sha256sum -c SHA256SUMS >/dev/null
)
tail -n 20 "$backup_dir/database.sql" | grep -q '^-- Dump completed' || die "database dump lacks completion marker"

while IFS= read -r entry; do
    case "$entry" in
        ""|/|/*|..|../*|*/../*|*/..) die "unsafe archive entry: $entry" ;;
    esac
done < <(tar -tf "$backup_dir/files.tar")
if ! tar -tf "$backup_dir/files.tar" | grep -qx 'env'; then
    die "files archive is missing env"
fi
if ! tar -tf "$backup_dir/files.tar" | grep -q '^kb/'; then
    die "files archive is missing kb"
fi
log "backup verification passed: $backup_dir"

printf '\nMANIFEST:\n' >&2
sed -n '1,20p' "$backup_dir/MANIFEST" >&2
cat >&2 <<EOF

Manual restore procedure (NOT executed by this script):
  1. Take a fresh backup and record the approved change window.
  2. systemctl stop $(cfg SCHEDULER_UNIT) $(cfg API_UNIT)
  3. mysql --defaults-extra-file=$(cfg MYSQL_DEFAULTS_FILE) --database=$(cfg MYSQL_DATABASE) < "$backup_dir/database.sql"
  4. tar -C $(cfg SHARED_DIR) -xpf "$backup_dir/files.tar" uploads kb
     Restore env separately only if credential rollback is intended:
     tar -C $(cfg SHARED_DIR) -xpf "$backup_dir/files.tar" env
  5. chown -R $(cfg SERVICE_USER):$(cfg SERVICE_GROUP) $(cfg UPLOAD_DIR) $(cfg KB_DIR)
  6. restorecon -Rv $(cfg SHARED_DIR)  # only on an Enforcing SELinux host
  7. systemctl start $(cfg API_UNIT) $(cfg SCHEDULER_UNIT)
  8. curl -fsS http://$(cfg API_HOST):$(cfg API_PORT)/health && journalctl -u $(cfg API_UNIT) -n 50

Database restore is not reversible. Verify the dump at step 3 with a disposable
instance before touching production, and follow the encrypted/off-host handling
policy. MySQL credentials are read only from the 0600 defaults-extra-file.
EOF
