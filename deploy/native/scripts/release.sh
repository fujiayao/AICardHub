#!/usr/bin/env bash
# aicardhub-native: install a prebuilt release and optionally activate it.
set -Eeuo pipefail
IFS=$'\n\t'
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

usage() {
    cat >&2 <<'EOF'
Usage: release.sh --config FILE --artifact PATH --release-id ID [--activate]

The artifact is either a directory or a .tar/.tar.gz/.tgz with this root layout:
  server/  apps/h5/dist/  apps/admin/dist/  venv/
It must be built for EL9 x86_64 and Python 3.12. The script validates the
artifact, copies it under releases/<id>, makes it root-owned and read-only, and
atomically creates no symlink unless --activate is passed. It never builds,
installs packages, migrates the database, seeds data or copies shared data.
EOF
}

config=""
artifact=""
release_id=""
activate=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --config) config="${2:-}"; shift 2 ;;
        --artifact) artifact="${2:-}"; shift 2 ;;
        --release-id) release_id="${2:-}"; shift 2 ;;
        --activate) activate=1; shift ;;
        --help|-h) usage; exit 0 ;;
        *) usage; die "unknown argument: $1" ;;
    esac
done
[ -n "$config" ] || { usage; die "--config is required"; }
[ -n "$artifact" ] || { usage; die "--artifact is required"; }
[ -n "$release_id" ] || { usage; die "--release-id is required"; }
[[ "$release_id" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$ ]] || die "invalid release id"
case "$release_id" in current|.*|*..*) die "reserved release id" ;; esac
load_config "$config"
require_keys RELEASES_DIR CURRENT_LINK API_UNIT SCHEDULER_UNIT ENV_FILE MIGRATION_GATE_FILE DEPLOY_LOCK MAINTENANCE_LOCK PYTHON_RUNTIME
render_check "$config" >/dev/null
require_root
acquire_lock "$(cfg DEPLOY_LOCK)"
"$SCRIPT_DIR/preflight.sh" --config "$config" --mode install

releases_dir="$(cfg RELEASES_DIR)"
[ -d "$releases_dir" ] || die "releases directory missing; run install.sh/bootstrap.sh first"
[ ! -e "$releases_dir/$release_id" ] || die "release already exists: $release_id"
[ -e "$artifact" ] || die "artifact not found: $artifact"

py="$(config_python)" || die "python3/python is required for artifact validation"
validator="$SCRIPT_DIR/validate_artifact.py"
staging=""
cleanup() {
    if [ -n "${staging:-}" ] && [ -d "$staging" ]; then
        case "$staging" in
            "$releases_dir"/.staging-*) rm -rf -- "$staging" ;;
            *) warn "refusing to remove unexpected staging path: $staging" ;;
        esac
    fi
}
trap cleanup EXIT

if [ -d "$artifact" ]; then
    "$py" "$validator" --dir "$artifact"
    [ ! -L "$artifact" ] || die "artifact directory must not be a symlink"
    staging="$(mktemp -d "$releases_dir/.staging-$release_id.XXXXXX")"
    cp -a "$artifact/." "$staging/"
    artifact_kind="directory"
    artifact_sha="not-applicable"
elif [ -f "$artifact" ]; then
    "$py" "$validator" --archive "$artifact"
    staging="$(mktemp -d "$releases_dir/.staging-$release_id.XXXXXX")"
    case "$artifact" in
        *.tar.gz|*.tgz) tar -xzf "$artifact" -C "$staging" --no-same-owner ;;
        *.tar) tar -xf "$artifact" -C "$staging" --no-same-owner ;;
        *) die "unsupported archive type (use .tar, .tar.gz or .tgz)" ;;
    esac
    artifact_kind="archive"
    artifact_sha="$(sha256sum "$artifact" | awk '{print $1}')"
else
    die "artifact must be a directory or tar archive: $artifact"
fi

[ -n "$staging" ] || die "staging directory was not created"
"$py" "$validator" --dir "$staging"
[ -x "$staging/venv/bin/python" ] || die "release venv/bin/python is not executable"
"$staging/venv/bin/python" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)' \
    || die "release venv is not Python 3.12"

cat > "$staging/RELEASE-METADATA" <<EOF
release_id=$release_id
artifact_kind=$artifact_kind
artifact_sha256=$artifact_sha
installed_at=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
layout=server,apps/h5/dist,apps/admin/dist,venv
EOF
chmod 0644 "$staging/RELEASE-METADATA"
find "$staging" -type f -exec chown root:root {} + -exec chmod u+rw,go+r {} +
find "$staging" -type d -exec chown root:root {} + -exec chmod u+rwx,go+rx {} +
find "$staging" -type l -exec chown -h root:root {} +
final="$releases_dir/$release_id"
mv "$staging" "$final"
staging=""
log "release installed: $final"

if [ "$activate" -eq 1 ]; then
    log "activating release $release_id"
    "$SCRIPT_DIR/activate.sh" --config "$config" --release-id "$release_id" --lock-held
else
    log "release is staged only; run activate.sh when the migration gate is approved"
fi
