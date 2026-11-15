#!/usr/bin/env python3
"""Local, stdlib-only validation of the native deployment templates.

This is deliberately not a substitute for nginx -t or systemd-analyze verify on
an EL9 host. It checks renderer fixture output and security invariants that can
be checked portably from Windows/Linux.
"""

from __future__ import annotations

import argparse
import copy
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import render  # noqa: E402

NEGATIVE_CHECKS = 0
QUOTED_LOCATION_RE = re.compile(r'(?m)^[ \t]*location[ \t]+~[ \t]+"([^"]+)"[ \t]*\{')


class ValidationError(AssertionError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def strip_comments(text: str) -> str:
    lines: list[str] = []
    for line in text.split("\n"):
        in_single = False
        in_double = False
        escaped = False
        kept: list[str] = []
        for char in line:
            if escaped:
                kept.append(char)
                escaped = False
                continue
            if char == "\\" and in_double:
                kept.append(char)
                escaped = True
                continue
            if char == "'" and not in_double:
                in_single = not in_single
                kept.append(char)
                continue
            if char == '"' and not in_single:
                in_double = not in_double
                kept.append(char)
                continue
            if char == "#" and not in_single and not in_double:
                break
            kept.append(char)
        lines.append("".join(kept))
    return "\n".join(lines)


def block(text: str, header: str) -> str:
    start = text.find(header)
    require(start >= 0, f"missing block: {header}")
    in_single = False
    in_double = False
    escaped = False
    brace = -1
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_double:
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if in_single or in_double:
            continue
        if char == "{" and not re.match(r"\{\d+(?:,\d*)?\}", text[index:]):
            brace = index
            break
    require(brace >= 0, f"missing opening brace: {header}")
    depth = 0
    in_single = False
    in_double = False
    escaped = False
    for index in range(brace, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_double:
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if in_single or in_double:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[brace + 1 : index]
    raise ValidationError(f"unclosed block: {header}")


def has(text: str, needle: str, label: str | None = None) -> None:
    require(needle in text, label or f"missing: {needle}")


def lacks(text: str, needle: str, label: str | None = None) -> None:
    require(needle not in text, label or f"unexpected: {needle}")


def location_paths(text: str) -> list[str]:
    pattern = re.compile(r"(?m)^\s*location\s+(?:(?:=|\^~|~\*|~)\s+)?([^\s{]+)\s*\{")
    paths = pattern.findall(text)
    return [path.strip('"') for path in paths]


def quoted_location(text: str, needle: str) -> re.Match[str]:
    for match in QUOTED_LOCATION_RE.finditer(text):
        if needle in match.group(1):
            return match
    raise ValidationError(f"missing quoted-regex location containing {needle}")


def check_locations(text: str, values: dict[str, str]) -> None:
    visible = strip_comments(text)
    uploads = values["UPLOAD_DIR"]
    h5 = values["H5_DIR"]
    admin = values["ADMIN_DIR"]
    require(h5 == values["CURRENT_LINK"] + "/apps/h5/dist", "H5 alias must target current/apps/h5/dist")
    require(admin == values["CURRENT_LINK"] + "/apps/admin/dist", "admin alias must target current/apps/admin/dist")

    lacks(visible, "server {", "locations include must not define a server")
    for directive in (
        "listen ",
        "server_name ",
        "ssl_certificate",
        "upstream ",
        "limit_req_zone",
        "limit_conn_zone",
        "proxy_cache_path",
        "gzip ",
        "gzip_",
        "root ",
        "try_files",
    ):
        lacks(visible, directive, f"location include must not contain {directive}")
    lacks(visible, "location / {", "must not own the host root")

    paths = location_paths(visible)
    require(len(paths) == 15, f"expected 15 prefix-anchored locations, found {len(paths)}: {paths}")
    for path in paths:
        require(
            path == "/aicardhub" or path.startswith("/aicardhub/") or path.startswith("^/aicardhub/"),
            f"location is not anchored under /aicardhub: {path}",
        )

    dot_match = quoted_location(visible, "/(?:.*/)?")
    dot_regex = dot_match.group(1)
    require(dot_regex == r"^/aicardhub/(?:.*/)?\.", "dotfile denial must use the nested-path quoted regex")
    dot_pattern = re.compile(dot_regex)
    for denied in ("/aicardhub/.git", "/aicardhub/admin/x/.env"):
        require(dot_pattern.match(denied), f"dotfile denial does not match {denied}")
    require(not dot_pattern.match("/aicardhub/assets/app.js"), "dotfile denial matches normal assets")

    files_match = quoted_location(visible, "/files/")
    files_regex = files_match.group(1)
    quoted_locations = list(QUOTED_LOCATION_RE.finditer(visible))
    require(quoted_locations[0].start() == dot_match.start(), "dotfile denial must be the first app regex location")
    require(files_match.start() > dot_match.start(), "dotfile denial must precede files regex")

    api = block(visible, "location /aicardhub/api/ {")
    short = block(visible, "location /aicardhub/c/ {")
    for label, section, suffix in (
        ("api", api, "/api/"),
        ("short link", short, "/c/"),
    ):
        has(section, f"proxy_pass http://{values['API_HOST']}:{values['API_PORT']}{suffix};", f"{label}: inline loopback proxy")
        has(section, "proxy_http_version 1.1;", f"{label}: HTTP/1.1")
        has(section, "proxy_buffering off;", f"{label}: buffering off")
        has(section, "proxy_request_buffering off;", f"{label}: request buffering off")
        has(section, "proxy_cache off;", f"{label}: cache off")
        has(section, "proxy_read_timeout 120s;", f"{label}: read timeout")
        has(section, "proxy_send_timeout 120s;", f"{label}: send timeout")
        has(section, "proxy_set_header X-Forwarded-Prefix /aicardhub;", f"{label}: forwarded prefix")
        has(section, "client_max_body_size 20m;", f"{label}: scoped body limit")
        lacks(section, "upstream ", f"{label}: no upstream")

    files = block(visible, files_match.group(0))
    has(files, f"alias {uploads}/$1;", "files alias must use capture")
    has(files, "disable_symlinks on;", "files must disable symlinks")
    has(files, "limit_except GET", "files must only allow GET/HEAD")
    has(files, "deny all;", "files other methods denied")
    has(files, "default_type application/octet-stream;")
    has(files, "image/jpeg jpg;")
    has(files, "image/png png;")
    for token in ("{32}", "-bg", "wechat", "qr", "poster", "\\.jpg", "\\.png", "[0-9a-z_:-]"):
        has(files_regex, token, f"files regex missing {token}")
    files_pattern = re.compile(files_regex)
    require(
        files_pattern.fullmatch("/aicardhub/files/" + "a" * 32 + ".jpg"),
        "files regex does not accept a legitimate UUID asset",
    )
    require(
        files_pattern.fullmatch("/aicardhub/files/my_card-1:staff-abc0123456-qr.png"),
        "files regex does not accept the project card-code alphabet",
    )
    require(
        files_pattern.fullmatch("/aicardhub/files/staff_1-a-abc0123456-poster.jpg"),
        "files regex does not accept a legal card code with a fixed hash suffix",
    )
    require(
        not files_pattern.fullmatch("/aicardhub/files/staff1-abc0123456-qr.PNG"),
        "files regex accepts an uppercase extension",
    )
    require(
        not files_pattern.fullmatch("/aicardhub/files/staff1-abc012345-qr.png"),
        "files regex accepts a wrong-length hash suffix",
    )
    require(
        not files_pattern.fullmatch("/aicardhub/files/../../shared/env"),
        "files regex accepts path traversal",
    )
    require(
        not files_pattern.fullmatch("/aicardhub/files/foo.php.jpg"),
        "files regex accepts a rejected .php.jpg name",
    )
    for forbidden in ("proxy_pass", "try_files", "root ", "php", "JPG", "PNG"):
        lacks(files, forbidden, f"files block must not contain {forbidden}")

    fallback = block(visible, "location /aicardhub/files/ {")
    has(fallback, "return 404;")
    for forbidden in ("proxy_pass", "alias", "root ", "try_files", "return 200"):
        lacks(fallback, forbidden, f"files fallback must not contain {forbidden}")
    has(block(visible, "location = /aicardhub/files {"), "return 404;")

    admin_redirect = block(visible, "location = /aicardhub/admin {\n")
    has(admin_redirect, "return 301 /aicardhub/admin/;")
    admin_index = block(visible, "location = /aicardhub/admin/index.html {")
    has(admin_index, f"alias {admin}/index.html;")
    admin_assets = block(visible, "location /aicardhub/admin/assets/ {")
    has(admin_assets, f"alias {admin}/assets/;")
    lacks(admin_assets, "try_files", "missing admin assets must 404")
    lacks(admin_assets, "disable_symlinks", "release assets must allow the current symlink")
    for forbidden in ("error_page", "proxy_pass", "return 200"):
        lacks(admin_assets, forbidden, f"missing admin assets must not use {forbidden}")
    admin_spa = block(visible, "location /aicardhub/admin/ {")
    has(admin_spa, f"alias {admin}/;")
    has(admin_spa, "error_page 404 =200 /aicardhub/admin/index.html;")
    lacks(admin_spa, "try_files", "admin fallback must use a safe alias/error_page")

    h5_root = block(visible, "location = /aicardhub/ {")
    has(h5_root, "rewrite ^ /aicardhub/index.html last;")
    lacks(h5_root, "alias ", "H5 slash root must rewrite to exact index instead of file alias")
    h5_index = block(visible, "location = /aicardhub/index.html {")
    has(h5_index, f"alias {h5}/index.html;")
    h5_assets = block(visible, "location /aicardhub/assets/ {")
    has(h5_assets, f"alias {h5}/assets/;")
    lacks(h5_assets, "try_files", "missing H5 assets must 404")
    lacks(h5_assets, "disable_symlinks", "release assets must allow the current symlink")
    for forbidden in ("error_page", "proxy_pass", "return 200"):
        lacks(h5_assets, forbidden, f"missing H5 assets must not use {forbidden}")
    h5_spa = block(visible, "location /aicardhub/ {")
    has(h5_spa, f"alias {h5}/;")
    has(h5_spa, "error_page 404 =200 /aicardhub/index.html;")
    lacks(h5_spa, "try_files", "H5 fallback must use a safe alias/error_page")

    has(visible, "location = /aicardhub {\n    return 301 /aicardhub/;")
    for forbidden in ("fastcgi_pass", "uwsgi_pass", "scgi_pass", "cgi_pass", "autoindex on"):
        lacks(visible, forbidden, f"unexpected directive {forbidden}")
    lacks(visible, f"alias {values['KB_DIR']}", "kb must never be served")
    lacks(visible, f"root {values['SHARED_DIR']};", "shared directory must never be a web root")
    require(visible.count("{") == visible.count("}"), "location braces are unbalanced")


def check_stage(text: str, values: dict[str, str]) -> None:
    visible = strip_comments(text)
    require(visible.count("server {") == 1, "stage wrapper must contain exactly one server")
    has(visible, "listen 127.0.0.1:18080;", "stage must bind loopback only")
    has(visible, "server_name localhost;", "stage server_name must be localhost")
    has(visible, f"include {values['NGINX_INCLUDE_FILE']};", "stage must include the prefix locations")
    lacks(visible, "listen 443", "stage must not listen on 443")
    lacks(visible, "listen 80", "stage must not listen on 80")
    lacks(visible, "ssl_certificate", "stage must not terminate TLS")
    lacks(visible, "root ", "stage must not define a root outside the prefix")
    lacks(visible, "proxy_pass", "stage wrapper must only include the shared locations")
    require(visible.count("{") == visible.count("}"), "stage braces are unbalanced")


def check_systemd(api: str, scheduler: str, backup: str, timer: str, values: dict[str, str]) -> None:
    user = values["SERVICE_USER"]
    current = values["CURRENT_LINK"]
    for name, text in (("api", api), ("scheduler", scheduler)):
        has(text, f"User={user}", f"{name}: service user")
        has(text, f"Group={values['SERVICE_GROUP']}", f"{name}: service group")
        has(text, f"WorkingDirectory={current}/server", f"{name}: working directory")
        has(text, f"EnvironmentFile={values['ENV_FILE']}", f"{name}: env file")
        has(text, f"ReadWritePaths={values['UPLOAD_DIR']} {values['KB_DIR']}", f"{name}: writable paths")
        has(text, "ProtectSystem=strict", f"{name}: strict filesystem")
        has(text, "NoNewPrivileges=true", f"{name}: no new privileges")
        has(text, "Restart=always", f"{name}: restart policy")
        has(text, "PYTHONDONTWRITEBYTECODE=1", f"{name}: no bytecode writes")
        lacks(text, "0.0.0.0", f"{name}: must not bind all interfaces")
        lacks(text, "alembic", f"{name}: migrations are not run by systemd")
        lacks(text, "PUBLIC_BASE_URL=https://haiwex.com", f"{name}: env belongs in EnvironmentFile")
    expected = (
        f"ExecStart={current}/venv/bin/python -m uvicorn app.main:app "
        f"--host {values['API_HOST']} --port {values['API_PORT']} --workers 1 "
        "--root-path /aicardhub --no-server-header --proxy-headers --forwarded-allow-ips=127.0.0.1"
    )
    has(api, expected, "api: exact loopback one-worker root-path command")
    has(api, f"MemoryMax={values['API_MEMORY_MAX']}")
    has(scheduler, f"ExecStart={current}/venv/bin/python -m app.scheduler", "scheduler: independent process")
    has(scheduler, f"MemoryMax={values['SCHEDULER_MEMORY_MAX']}")
    has(backup, "User=root")
    has(backup, f"ExecStart={values['OPS_DIR']}/backup.sh --config {values['BACKUP_ENV_FILE']}")
    has(backup, "UMask=0077")
    has(timer, f"Unit={values['BACKUP_UNIT']}")
    has(timer, "OnCalendar=*-*-* 02:30:00")


def check_logrotate(text: str, values: dict[str, str]) -> None:
    visible = strip_comments(text)
    for path in (values["NGINX_ACCESS_LOG"], values["NGINX_ERROR_LOG"], values["BACKUP_LOG"]):
        has(visible, path)
    lacks(visible, "/var/log/nginx/*.log", "must not rotate every nginx log")
    lacks(visible, "journalctl", "must not change journald policy")
    has(visible, "kill -USR1")
    has(visible, f"create 0640 {values['NGINX_USER']} {values['NGINX_LOG_GROUP']}")
    has(visible, f"su root {values['NGINX_LOG_GROUP']}")


def check_outputs(written: dict[str, Path], values: dict[str, str]) -> None:
    require(len(written) == 7, "expected seven rendered files")
    for name, path in written.items():
        require(path.is_file(), f"missing rendered file {name}")
        raw = path.read_bytes()
        require(b"\r" not in raw, f"{name}: CRLF is not allowed")
        require(raw.endswith(b"\n"), f"{name}: must end with newline")
        text = raw.decode("utf-8")
        first_line = text.split("\n", 1)[0]
        require(
            first_line == render.GENERATED_MARKER,
            f"{name}: first line must be exactly the standalone generated marker",
        )
        require("@@" not in text, f"{name}: unresolved template token")
    locations = written["aicardhub.locations.conf"].read_text(encoding="utf-8")
    stage = written["aicardhub.stage.conf"].read_text(encoding="utf-8")
    api = written[values["API_UNIT"]].read_text(encoding="utf-8")
    scheduler = written[values["SCHEDULER_UNIT"]].read_text(encoding="utf-8")
    backup = written[values["BACKUP_UNIT"]].read_text(encoding="utf-8")
    timer = written[values["BACKUP_TIMER"]].read_text(encoding="utf-8")
    logrotate = written[values["SITE_NAME"] + ".logrotate"].read_text(encoding="utf-8")
    check_locations(locations, values)
    check_stage(stage, values)
    check_systemd(api, scheduler, backup, timer, values)
    check_logrotate(logrotate, values)


def expect_invalid(base: dict[str, str], label: str, mutate, *, production: bool = False) -> None:
    global NEGATIVE_CHECKS
    values = copy.deepcopy(base)
    mutate(values)
    try:
        render.validate_config(values, production=production)
    except render.ConfigError:
        NEGATIVE_CHECKS += 1
        return
    raise ValidationError(f"negative config test did not fail: {label}")


def check_negative_config(values: dict[str, str], config_path: Path) -> None:
    global NEGATIVE_CHECKS
    expect_invalid(values, "0.0.0.0 API host", lambda v: v.update(API_HOST="0.0.0.0"))
    expect_invalid(values, "two workers", lambda v: v.update(API_WORKERS="2"))
    expect_invalid(values, "privileged API port", lambda v: v.update(API_PORT="80"))
    expect_invalid(values, "backup under deploy root", lambda v: v.update(BACKUP_ROOT=values["DEPLOY_ROOT"] + "/backups"))
    expect_invalid(values, "env under uploads", lambda v: v.update(ENV_FILE=values["UPLOAD_DIR"] + "/env"))
    expect_invalid(values, "uploads equals kb", lambda v: v.update(UPLOAD_DIR=values["KB_DIR"]))
    expect_invalid(values, "uppercase site", lambda v: v.update(SITE_NAME="AICardHub"))
    expect_invalid(values, "wrong current link", lambda v: v.update(CURRENT_LINK=values["DEPLOY_ROOT"] + "/live"))
    expect_invalid(values, "reserved service user", lambda v: v.update(SERVICE_USER="root"))
    expect_invalid(values, "non-loopback stage bind", lambda v: v.update(STAGE_LISTEN="0.0.0.0:18080"))
    expect_invalid(values, "wrong stage port", lambda v: v.update(STAGE_LISTEN="127.0.0.1:18081"))
    expect_invalid(values, "public stage name", lambda v: v.update(STAGE_SERVER_NAME="haiwex.com"))
    expect_invalid(values, "include outside ops", lambda v: v.update(NGINX_INCLUDE_FILE=values["SHARED_DIR"] + "/locations.conf"))
    expect_invalid(values, "stage file outside ops", lambda v: v.update(STAGE_CONF_FILE=values["SHARED_DIR"] + "/stage.conf"))
    expect_invalid(values, "split maintenance locks", lambda v: v.update(MAINTENANCE_LOCK="/run/other.lock"))
    expect_invalid(values, "lock outside run", lambda v: v.update(DEPLOY_LOCK="/tmp/aicardhub.lock", MAINTENANCE_LOCK="/tmp/aicardhub.lock"))
    expect_invalid(values, "overlapping releases/shared", lambda v: v.update(SHARED_DIR=values["RELEASES_DIR"] + "/shared"))
    expect_invalid(values, "duplicate api scheduler unit", lambda v: v.update(SCHEDULER_UNIT=values["API_UNIT"]))
    expect_invalid(values, "duplicate backup unit", lambda v: v.update(BACKUP_UNIT=values["API_UNIT"]))
    expect_invalid(values, "memory max below high", lambda v: v.update(API_MEMORY_MAX="400M"))
    expect_invalid(values, "placeholder production domain", lambda v: v.update(SITE_DOMAIN="card.example.invalid"), production=True)

    def missing(values: dict[str, str]) -> None:
        del values["API_PORT"]

    expect_invalid(values, "missing key", missing)

    with tempfile.TemporaryDirectory(prefix="aicardhub-config-test-") as temp_name:
        temp = Path(temp_name)
        unsafe = temp / "unsafe.conf"
        unsafe.write_text(config_path.read_text(encoding="utf-8").replace("API_PORT=18000", "API_PORT=18000;reboot"), encoding="utf-8")
        try:
            render.load_config(unsafe)
        except render.ConfigError:
            NEGATIVE_CHECKS += 1
        else:
            raise ValidationError("unsafe config value was accepted")
        duplicate = temp / "duplicate.conf"
        duplicate.write_text(config_path.read_text(encoding="utf-8") + "API_PORT=18001\n", encoding="utf-8")
        try:
            render.load_config(duplicate)
        except render.ConfigError:
            NEGATIVE_CHECKS += 1
        else:
            raise ValidationError("duplicate key was accepted")
        crlf = temp / "crlf.conf"
        crlf.write_bytes(config_path.read_bytes().replace(b"\n", b"\r\n"))
        try:
            render.load_config(crlf)
        except render.ConfigError:
            NEGATIVE_CHECKS += 1
        else:
            raise ValidationError("CRLF config was accepted")


def check_repo_files(root: Path) -> None:
    text_suffixes = {".sh", ".py", ".in", ".example", ".md", ".conf", ".service", ".timer", ".logrotate"}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in text_suffixes:
            continue
        raw = path.read_bytes()
        require(b"\r" not in raw, f"{path}: CRLF is not allowed")
    for path in (root / "scripts").glob("*.sh"):
        text = path.read_text(encoding="utf-8")
        require(text.startswith("#!/usr/bin/env bash\n"), f"{path}: missing bash shebang")
    for path in sorted((root / "templates").rglob("*.in")):
        first_line = path.read_text(encoding="utf-8").split("\n", 1)[0]
        require(
            first_line == render.GENERATED_MARKER,
            f"{path}: template first line must be exactly the standalone generated marker",
        )
    require(not (root / "templates" / "nginx" / "aicardhub.conf.in").exists(), "obsolete standalone vhost template still present")

    backup_env = (root / "templates" / "backup.env.example").read_text(encoding="utf-8")
    backup_keys = {
        "DEPLOY_ROOT",
        "BACKUP_ROOT",
        "BACKUP_RETENTION_DAYS",
        "BACKUP_LOG",
        "LOG_DIR",
        "LOG_GROUP",
        "MYSQL_DEFAULTS_FILE",
        "MYSQL_DATABASE",
        "MYSQL_DUMP_BIN",
        "API_HOST",
        "API_PORT",
        "SERVICE_USER",
        "SERVICE_GROUP",
        "SHARED_DIR",
        "UPLOAD_DIR",
        "KB_DIR",
        "ENV_FILE",
        "RELEASES_DIR",
        "CURRENT_LINK",
        "API_UNIT",
        "SCHEDULER_UNIT",
        "DEPLOY_LOCK",
        "MAINTENANCE_LOCK",
    }
    for key in sorted(backup_keys):
        require(f"\n{key}=" in "\n" + backup_env, f"backup.env.example missing {key}")
    app_env = (root / "templates" / "app.env.example").read_text(encoding="utf-8")
    require("AICARD_ROOT_PATH=/aicardhub" in app_env, "app.env.example missing AICARD_ROOT_PATH")
    require(
        "AICARD_POSTER_FONT_PATH=/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc" in app_env,
        "app.env.example missing the documented CJK font path",
    )
    require(
        "PUBLIC_BASE_URL=https://haiwex.com/aicardhub" in app_env,
        "app.env.example must use the authorized public prefix URL",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate AICardHub native deployment fixtures")
    parser.add_argument("--config", type=Path, default=HERE.parent / "aicardhub.conf.example")
    parser.add_argument("--render-dir", type=Path, help="use existing rendered output instead of rendering")
    args = parser.parse_args(argv)
    try:
        values = render.build_context(render.validate_config(render.load_config(args.config)))
        if args.render_dir:
            names = {
                "aicardhub.locations.conf",
                "aicardhub.stage.conf",
                values["API_UNIT"],
                values["SCHEDULER_UNIT"],
                values["BACKUP_UNIT"],
                values["BACKUP_TIMER"],
                values["SITE_NAME"] + ".logrotate",
            }
            written = {name: args.render_dir / name for name in names}
            check_outputs(written, values)
        else:
            with tempfile.TemporaryDirectory(prefix="aicardhub-validate-") as temp_name:
                written = render.render_to(args.config, Path(temp_name))
                check_outputs(written, values)
        check_negative_config(values, args.config)
        check_repo_files(HERE.parent)
        with tempfile.TemporaryDirectory(prefix="aicardhub-production-test-") as temp_name:
            render.render_to(args.config, Path(temp_name), production=True)
        print("validation passed")
        print("  nginx invariants: prefix-only locations, nested-dot deny first, 200 SPA fallbacks, SSE buffering off, 120s timeouts")
        print("  stage invariant: single loopback 127.0.0.1:18080 server, no TLS/root/public listen")
        print("  systemd invariants: aicardhub user, loopback one worker with /aicardhub root-path, independent scheduler")
        print(f"  negative config tests: {NEGATIVE_CHECKS} (including parser and production-placeholder checks)")
        print("  line endings: LF only")
        return 0
    except (ValidationError, render.ConfigError) as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
