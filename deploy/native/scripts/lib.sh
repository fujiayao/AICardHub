#!/usr/bin/env bash
# aicardhub-native: shared shell helpers. Never source the product environment.
set -Eeuo pipefail
IFS=$'\n\t'
readonly GENERATED_MARKER="# aicardhub-native: generated file"
readonly MANAGED_SHELL_PREFIX="# aicardhub-native: "

log() {
    printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*" >&2
}

warn() {
    printf '[%s] WARNING: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*" >&2
}

die() {
    printf '[%s] ERROR: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*" >&2
    exit 1
}

need_cmd() {
    command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

require_root() {
    [ "$(id -u)" -eq 0 ] || die "this action must run as root"
}

require_file() {
    [ -f "$1" ] || die "file not found: $1"
}

require_dir() {
    [ -d "$1" ] || die "directory not found: $1"
}

load_config() {
    local file="$1"
    local line key value
    [ -n "$file" ] || die "config path is required"
    [ -f "$file" ] || die "config not found: $file"
    [ ! -L "$file" ] || die "config must not be a symlink: $file"
    declare -gA CFG=()
    while IFS= read -r line || [ -n "$line" ]; do
        [[ "$line" == *$'\r'* ]] && die "config must use LF line endings"
        [ -z "$line" ] && continue
        [[ "$line" == \#* ]] && continue
        [[ "$line" =~ ^([A-Z][A-Z0-9_]*)=([^[:space:]]+)$ ]] || die "invalid config line: $line"
        key="${BASH_REMATCH[1]}"
        value="${BASH_REMATCH[2]}"
        # POSIX bracket expressions cannot reliably escape ']' across grep
        # implementations (Git Bash/MSYS in particular). Use a Bash pattern
        # with ']' first and '-' last so the class is unambiguous.
        [[ "$value" == *[!][A-Za-z0-9_./:@%+,-]* ]] \
            && die "unsafe config value for $key"
        [ -z "${CFG[$key]+x}" ] || die "duplicate config key: $key"
        CFG["$key"]="$value"
    done < "$file"
    CONFIG_FILE="$file"
}

cfg() {
    local key="$1"
    [ -n "${CFG[$key]+x}" ] || die "missing config key: $key"
    printf '%s' "${CFG[$key]}"
}

require_keys() {
    local key
    for key in "$@"; do
        [ -n "${CFG[$key]+x}" ] || die "missing config key: $key"
    done
}

file_mode() {
    stat -c '%a' "$1"
}

file_owner() {
    stat -c '%U:%G' "$1"
}

require_private_file() {
    local path="$1" label="$2" mode
    [ -e "$path" ] || die "$label not found: $path"
    [ -f "$path" ] || die "$label must be a regular file: $path"
    [ ! -L "$path" ] || die "$label must not be a symlink: $path"
    mode="$(file_mode "$path")"
    [ "$mode" = "600" ] || die "$label must be mode 0600, found $mode: $path"
    [ "$(stat -c '%U' "$path")" = "root" ] || die "$label must be owned by root: $path"
}

is_generated() {
    [ -f "$1" ] && [ ! -L "$1" ] \
        && [ "$(head -n 1 "$1")" = "$GENERATED_MARKER" ]
}

is_managed_shell() {
    local first second
    [ -f "$1" ] && [ ! -L "$1" ] || return 1
    first="$(head -n 1 "$1")"
    second="$(sed -n '2p' "$1")"
    [ "$first" = "#!/usr/bin/env bash" ] || return 1
    case "$second" in
        "$MANAGED_SHELL_PREFIX"*) return 0 ;;
        *) return 1 ;;
    esac
}

require_managed_or_absent() {
    local path="$1" kind="${2:-generated}"
    [ ! -L "$path" ] || die "refusing to overwrite symlink target: $path"
    [ ! -e "$path" ] && return 0
    case "$kind" in
        generated) is_generated "$path" ;;
        shell) is_managed_shell "$path" ;;
        *) die "unknown managed-file kind: $kind" ;;
    esac || die "refusing to overwrite unmanaged file: $path"
}

install_generated() {
    local source="$1" target="$2" mode="${3:-0644}" kind="${4:-generated}"
    [ -f "$source" ] || die "rendered file missing: $source"
    mkdir -p "$(dirname "$target")"
    require_managed_or_absent "$target" "$kind"
    install -m "$mode" -o root -g root "$source" "$target"
}

install_managed_shell() {
    install_generated "$1" "$2" "${3:-0644}" shell
}

atomic_symlink() {
    local target="$1" link="$2" temp
    [ -d "$(dirname "$link")" ] || die "symlink parent missing: $link"
    temp="$(dirname "$link")/.$(basename "$link").$$"
    rm -f "$temp"
    ln -s "$target" "$temp"
    mv -Tf "$temp" "$link"
}

read_link_target() {
    local link="$1"
    [ -L "$link" ] || return 1
    readlink -f "$link"
}

acquire_lock() {
    local path="$1"
    local canonical
    need_cmd flock
    canonical="$(readlink -m "$path")" || die "cannot normalize lock path: $path"
    [ "$canonical" = "$path" ] || die "lock path must be normalized: $path (expected $canonical)"
    mkdir -p "$(dirname "$path")"
    exec 9>"$path"
    flock -n 9 || die "another deployment/maintenance operation holds $path"
}

python_bin() {
    if [ -n "${PYTHON_BIN:-}" ]; then
        printf '%s' "$PYTHON_BIN"
        return
    fi
    if command -v python3 >/dev/null 2>&1; then
        command -v python3
    elif command -v python >/dev/null 2>&1; then
        command -v python
    else
        return 1
    fi
}

config_python() {
    if [ -n "${CFG[PYTHON_RUNTIME]+x}" ] && [ -x "${CFG[PYTHON_RUNTIME]}" ]; then
        printf '%s' "${CFG[PYTHON_RUNTIME]}"
        return 0
    fi
    python_bin
}

render_check() {
    local config="$1" py
    py="$(config_python)" || die "python3/python is required for rendering"
    "$py" "$(dirname "${BASH_SOURCE[0]}")/render.py" --check --config "$config"
}

service_active() {
    systemctl is-active --quiet "$1" 2>/dev/null
}

health_check() {
    local url="$1" attempts="${2:-30}" delay="${3:-1}" i
    for ((i = 1; i <= attempts; i++)); do
        if curl -fsS --max-time 3 "$url" >/dev/null 2>&1; then
            return 0
        fi
        sleep "$delay"
    done
    return 1
}
