#!/usr/bin/env bash
# aicardhub-native: thin renderer wrapper. Rendering is the default, read-only action.
set -Eeuo pipefail
IFS=$'\n\t'
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
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
exec "$py" "$SCRIPT_DIR/render.py" "$@"
