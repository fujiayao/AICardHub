#!/usr/bin/env bash
# aicardhub-native: local fixture/invariant verification (not an EL9 acceptance run).
set -Eeuo pipefail
IFS=$'\n\t'
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
if [ -n "${PYTHON_BIN:-}" ]; then
    py="$PYTHON_BIN"
elif command -v python3 >/dev/null 2>&1; then
    py="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
    py="$(command -v python)"
else
    printf 'ERROR: python3 or python is required\n' >&2
    exit 1
fi

tmp="$(mktemp -d)"
cleanup() {
    case "$tmp" in
        /tmp/*|*/tmp/*|*aicardhub-verify*) rm -rf -- "$tmp" ;;
        *) printf 'refusing to remove unexpected temp path: %s\n' "$tmp" >&2 ;;
    esac
}
trap cleanup EXIT

printf '== render ==\n'
"$py" "$SCRIPT_DIR/render.py" --config "$ROOT/aicardhub.conf.example" --out "$tmp/render"

printf '== template/config invariants ==\n'
"$py" "$SCRIPT_DIR/validate.py" --config "$ROOT/aicardhub.conf.example" --render-dir "$tmp/render"

printf '== shell syntax ==\n'
for script in "$SCRIPT_DIR"/*.sh; do
    bash -n "$script"
    printf 'ok: %s\n' "$(basename "$script")"
done

printf '== CLI help and bootstrap dry-run ==\n'
bash "$SCRIPT_DIR/bootstrap.sh" --config "$ROOT/aicardhub.conf.example" >/dev/null
for script in install backup restore release activate rollback preflight; do
    bash "$SCRIPT_DIR/$script.sh" --help >/dev/null 2>&1
done
printf 'ok: bootstrap dry-run and help entry points\n'

printf '== managed-shell detection ==\n'
managed="$tmp/managed.sh"
printf '#!/usr/bin/env bash\n# aicardhub-native: fixture helper\n' >"$managed"
(
    # shellcheck source=lib.sh
    . "$SCRIPT_DIR/lib.sh"
    is_managed_shell "$managed"
)
generated="$tmp/generated.conf"
printf '# aicardhub-native: generated file\nkey=value\n' >"$generated"
(
    # shellcheck source=lib.sh
    . "$SCRIPT_DIR/lib.sh"
    is_generated "$generated"
)
if [ -e "$tmp/link.sh" ] || ln -s "$managed" "$tmp/link.sh" 2>/dev/null; then
    if (
        # shellcheck source=lib.sh
        . "$SCRIPT_DIR/lib.sh"
        is_managed_shell "$tmp/link.sh"
    ); then
        printf 'ERROR: managed-shell detection accepted a symlink\n' >&2
        exit 1
    fi
fi
printf 'ok: generated marker and managed shell header accepted; symlink rejected\n'

printf '== release artifact validator fixture ==\n'
fixture="$tmp/artifact"
mkdir -p "$fixture/server/app" "$fixture/server/alembic" "$fixture/apps/h5/dist/assets" "$fixture/apps/admin/dist/assets" "$fixture/venv/bin"
printf '#!/bin/sh\n' >"$fixture/server/app/main.py"
printf '#!/bin/sh\n' >"$fixture/server/app/scheduler.py"
printf '[alembic]\n' >"$fixture/server/alembic.ini"
printf 'version = 1\n' >"$fixture/server/uv.lock"
printf '[project]\nname = "fixture"\n' >"$fixture/server/pyproject.toml"
printf '<!doctype html>\n' >"$fixture/apps/h5/dist/index.html"
printf '<!doctype html>\n' >"$fixture/apps/admin/dist/index.html"
printf '# fixture\n' >"$fixture/venv/pyvenv.cfg"
printf '#!/bin/sh\n' >"$fixture/venv/bin/python"
chmod +x "$fixture/venv/bin/python"
"$py" "$SCRIPT_DIR/validate_artifact.py" --dir "$fixture"
tar -czf "$tmp/artifact.tar.gz" -C "$fixture" server apps venv
"$py" "$SCRIPT_DIR/validate_artifact.py" --archive "$tmp/artifact.tar.gz"
"$py" - "$SCRIPT_DIR" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
import validate_artifact

validate_artifact.safe_link_target("venv/bin/python", "/usr/bin/python3.12", {"venv/bin/python"})
try:
    validate_artifact.safe_link_target("venv/bin/python", "/etc/passwd", {"venv/bin/python"})
except validate_artifact.ArtifactError:
    pass
else:
    raise SystemExit("unvalidated absolute Python symlink accepted")
print("ok: validated system Python 3.12 symlink allowed, other absolute links rejected")
PY
"$py" - "$tmp/evil.tar.gz" <<'PY'
import sys, tarfile
with tarfile.open(sys.argv[1], "w:gz") as archive:
    entry = tarfile.TarInfo("server/app/evil")
    entry.type = tarfile.SYMTYPE
    entry.linkname = "../../../../etc/passwd"
    archive.addfile(entry)
PY
if "$py" "$SCRIPT_DIR/validate_artifact.py" --archive "$tmp/evil.tar.gz" >/dev/null 2>&1; then
    printf 'ERROR: unsafe symlink archive was accepted\n' >&2
    exit 1
fi
printf 'ok: escaping symlink archive rejected\n'

printf '== line endings ==\n'
"$py" - "$ROOT" <<'PY'
import pathlib, sys
root = pathlib.Path(sys.argv[1])
for path in root.rglob("*"):
    if path.is_file() and path.suffix in {".sh", ".py", ".in", ".example", ".md", ".conf"}:
        data = path.read_bytes()
        if b"\r" in data:
            raise SystemExit(f"CRLF found: {path}")
print("ok: LF only")
PY

printf '\nlocal verification passed. nginx -t, systemd-analyze verify, live SSE and DB backup/restore were not run.\n'
