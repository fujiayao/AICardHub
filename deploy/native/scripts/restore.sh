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

Verifies MANIFEST, an exact two-path SHA256SUMS, database.sql completion marker and
the files archive structure (only env plus uploads/kb regular files and
directories; no links, devices, FIFOs, absolute, traversal or duplicate paths),
then prints the manual restore steps. It does not stop services, run mysql,
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
[ "$backup_dir" != */ ] || die "backup directory must not end with a slash"
[ "$(dirname -- "$backup_dir")" = "$backup_root" ] \
    || die "backup directory must be a direct child of BACKUP_ROOT"
case "${backup_dir##*/}" in
    aicardhub-backup-?*) ;;
    *) die "backup directory name must be aicardhub-backup-<timestamp>" ;;
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

# The checksum list may name only the two exact archive/report files. Refuse
# extra, duplicate or path-bearing entries before sha256sum reads them.
checksum_seen=""
while IFS= read -r line || [ -n "$line" ]; do
    [ -n "$line" ] || die "SHA256SUMS contains an empty line"
    [[ "$line" =~ ^[0-9a-f]{64}\ [\ *](database\.sql|files\.tar)$ ]] \
        || die "SHA256SUMS contains an unexpected entry: $line"
    name="${BASH_REMATCH[1]}"
    case " $checksum_seen " in
        *" $name "*) die "SHA256SUMS lists $name more than once" ;;
    esac
    checksum_seen="$checksum_seen $name"
done < "$backup_dir/SHA256SUMS"
for required in database.sql files.tar; do
    case " $checksum_seen " in
        *" $required "*) ;;
        *) die "SHA256SUMS does not cover $required" ;;
    esac
done
(
    cd "$backup_dir"
    sha256sum -c SHA256SUMS >/dev/null
)
tail -n 20 "$backup_dir/database.sql" | grep -q '^-- Dump completed' || die "database dump lacks completion marker"

# Parse the archive structurally: regular files and directories only, with
# exactly the env file plus uploads/ and kb/ trees. Symlinks, hardlinks,
# devices, FIFOs, absolute paths, traversal and duplicate names are rejected.
archive_check() {
    local archive="$1" py
    py="$(config_python)" || die "python3 is required to verify the files archive"
    "$py" -I - "$archive" <<'PY'
import sys
import tarfile
from pathlib import PurePosixPath

allowed_roots = {"env", "uploads", "kb"}
try:
    with tarfile.open(sys.argv[1], "r:*") as handle:
        members = handle.getmembers()
except (tarfile.TarError, OSError) as exc:
    print(f"cannot parse files archive: {exc}", file=sys.stderr)
    raise SystemExit(2)

seen = set()
roots = set()
has_env = False
for member in members:
    name = member.name
    if not name:
        raise SystemExit("files archive contains an empty member name")
    pure = PurePosixPath(name)
    if pure.is_absolute():
        raise SystemExit(f"files archive contains an absolute path: {name}")
    parts = pure.parts
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise SystemExit(f"files archive contains a traversal path: {name}")
    if name in seen:
        raise SystemExit(f"files archive contains a duplicate path: {name}")
    seen.add(name)
    root = parts[0]
    if root not in allowed_roots:
        raise SystemExit(f"files archive contains an unexpected top-level entry: {name}")
    roots.add(root)
    if member.isdir():
        continue
    if not member.isreg():
        raise SystemExit(f"files archive contains a non-regular member: {name}")
    if root == "env":
        if name != "env":
            raise SystemExit(f"env must be a single regular file: {name}")
        has_env = True
if not has_env:
    raise SystemExit("files archive is missing the env regular file")
for required in ("uploads", "kb"):
    if required not in roots:
        raise SystemExit(f"files archive is missing {required}")
print(f"files archive structure ok: {len(members)} members")
PY
}

archive_check "$backup_dir/files.tar"
log "backup verification passed: $backup_dir"

printf '\nMANIFEST:\n' >&2
sed -n '1,20p' "$backup_dir/MANIFEST" >&2
cat >&2 <<EOF

Manual restore procedure (NOT executed by this script):
  1. Take a fresh backup, record the approved change window and independent authorization.
  2. systemctl stop $(cfg SCHEDULER_UNIT) $(cfg API_UNIT)
     If either stop fails, stop here: do not run mysql and do not move directories.
  3. mysql --defaults-extra-file=$(cfg MYSQL_DEFAULTS_FILE) --database=$(cfg MYSQL_DATABASE) < "$backup_dir/database.sql"
  4. staging="\$(mktemp -d $(cfg SHARED_DIR).restore-staging.XXXXXX)"
     This staging directory is empty and on the same filesystem as $(cfg SHARED_DIR).
  5. tar -C "\$staging" -xpf "$backup_dir/files.tar"
     Extract only this already-validated archive, and only into the empty staging directory.
  6. Retain the live data, then move the staged directories into place (no rm -rf, no overlay):
       mv $(cfg UPLOAD_DIR) $(cfg UPLOAD_DIR).retained-<timestamp>
       mv $(cfg KB_DIR) $(cfg KB_DIR).retained-<timestamp>
       mv "\$staging/uploads" $(cfg UPLOAD_DIR)
       mv "\$staging/kb" $(cfg KB_DIR)
     Keep the retained sibling directories until the restore is verified and approved for deletion.
  7. env is NOT restored by default. Restore it separately only with explicit credential
     rollback authorization, keeping the old file:
       mv $(cfg ENV_FILE) $(cfg ENV_FILE).retained-<timestamp>
       mv "\$staging/env" $(cfg ENV_FILE)
     Otherwise leave "\$staging/env" in staging and do not copy it.
  8. chown -R $(cfg SERVICE_USER):$(cfg SERVICE_GROUP) $(cfg UPLOAD_DIR) $(cfg KB_DIR)
  9. restorecon -Rv $(cfg SHARED_DIR)  # only on an Enforcing SELinux host
 10. systemctl start $(cfg API_UNIT)
     curl -fsS http://$(cfg API_HOST):$(cfg API_PORT)/health
     Start the scheduler ONLY after the API health check succeeds:
     systemctl start $(cfg SCHEDULER_UNIT)
 11. If any step after stopping the services fails: leave BOTH units stopped, do not start
     the scheduler, keep the retained directories and staging contents, and escalate.

Database restore is not reversible. Verify the dump at step 3 with a disposable
instance before touching production, and follow the encrypted/off-host handling
policy. MySQL credentials are read only from the 0600 defaults-extra-file.
EOF
