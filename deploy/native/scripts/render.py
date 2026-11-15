#!/usr/bin/env python3
"""Render the AICardHub native EL9 deployment templates.

This is a stdlib-only renderer. It intentionally does not source shell files and
does not read the product environment or any credential file.
"""

from __future__ import annotations

import argparse
import posixpath
import re
import sys
from pathlib import Path
from typing import Any

GENERATED_MARKER = "# aicardhub-native: generated file"
TOKEN_RE = re.compile(r"@@([A-Z][A-Z0-9_]*)@@")
KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
SAFE_VALUE_RE = re.compile(r"^[A-Za-z0-9_./:@%+,\[\]-]+$")
SERVICE_RE = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")
UNIT_RE = re.compile(r"^[A-Za-z0-9@_.-]{1,96}\.service$")
TIMER_RE = re.compile(r"^[A-Za-z0-9@_.-]{1,96}\.timer$")
SITE_RE = re.compile(r"^[a-z][a-z0-9-]{1,30}$")
DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)
DB_RE = re.compile(r"^[A-Za-z0-9_]{1,64}$")
MEM_RE = re.compile(r"^[1-9][0-9]{0,5}[KMG]$")
VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){0,3}$")

REQUIRED_KEYS = frozenset(
    {
        "DEPLOY_ROOT",
        "SERVICE_NAME",
        "SERVICE_USER",
        "SERVICE_GROUP",
        "RELEASES_DIR",
        "SHARED_DIR",
        "UPLOAD_DIR",
        "KB_DIR",
        "LOG_DIR",
        "OPS_DIR",
        "CURRENT_LINK",
        "ENV_FILE",
        "MIGRATION_GATE_FILE",
        "DEPLOY_LOCK",
        "MAINTENANCE_LOCK",
        "PYTHON_RUNTIME",
        "VENV_DIR",
        "API_HOST",
        "API_PORT",
        "API_WORKERS",
        "API_UNIT",
        "SCHEDULER_UNIT",
        "BACKUP_UNIT",
        "BACKUP_TIMER",
        "API_MEMORY_HIGH",
        "API_MEMORY_MAX",
        "SCHEDULER_MEMORY_HIGH",
        "SCHEDULER_MEMORY_MAX",
        "SITE_NAME",
        "SITE_DOMAIN",
        "NGINX_INCLUDE_FILE",
        "STAGE_CONF_FILE",
        "STAGE_LISTEN",
        "STAGE_SERVER_NAME",
        "NGINX_USER",
        "NGINX_GROUP",
        "NGINX_PID_FILE",
        "NGINX_LOG_DIR",
        "NGINX_ACCESS_LOG",
        "NGINX_ERROR_LOG",
        "NGINX_LOG_GROUP",
        "LOGROTATE_CONF_DIR",
        "SYSTEMD_UNIT_DIR",
        "BACKUP_ROOT",
        "BACKUP_RETENTION_DAYS",
        "BACKUP_LOG",
        "BACKUP_ENV_FILE",
        "MYSQL_DEFAULTS_FILE",
        "MYSQL_DATABASE",
        "MYSQL_DUMP_BIN",
    }
)

RESERVED_ROOTS = {
    "/",
    "/bin",
    "/boot",
    "/dev",
    "/etc",
    "/home",
    "/lib",
    "/lib64",
    "/opt",
    "/proc",
    "/root",
    "/run",
    "/sbin",
    "/srv",
    "/sys",
    "/tmp",
    "/usr",
    "/var",
}


class ConfigError(ValueError):
    """Raised when deployment configuration is unsafe or incomplete."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ConfigError(message)


def load_config(path: Path) -> dict[str, str]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ConfigError(f"cannot read config: {exc}") from exc
    if b"\x00" in raw:
        raise ConfigError("config contains NUL bytes")
    if b"\r" in raw:
        raise ConfigError("config must use LF line endings")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ConfigError("config must be UTF-8") from exc
    values: dict[str, str] = {}
    for number, line in enumerate(text.split("\n"), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped != line:
            raise ConfigError(f"line {number}: leading or trailing whitespace is not allowed")
        if "=" not in line:
            raise ConfigError(f"line {number}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        _require(bool(KEY_RE.fullmatch(key)), f"line {number}: invalid key")
        _require(bool(value), f"line {number}: empty value")
        _require(bool(SAFE_VALUE_RE.fullmatch(value)), f"line {number}: unsafe character in value")
        _require(key not in values, f"line {number}: duplicate key {key}")
        values[key] = value
    missing = sorted(REQUIRED_KEYS - values.keys())
    _require(not missing, "missing config keys: " + ", ".join(missing))
    return values


def _abs_path(name: str, value: str, *, allow_root: bool = False) -> str:
    _require(value.startswith("/"), f"{name} must be absolute")
    _require("//" not in value, f"{name} must not contain '//'")
    _require(posixpath.normpath(value) == value, f"{name} must be normalized")
    _require(".." not in Path(value).parts, f"{name} must not contain '..'")
    if not allow_root:
        _require(value != "/", f"{name} must not be /")
    return value


def _under(child: str, parent: str) -> bool:
    return child == parent or child.startswith(parent.rstrip("/") + "/")


def _exact(child: str, parent: str, basename: str, name: str) -> None:
    _require(child == parent.rstrip("/") + "/" + basename, f"{name} must be {parent}/{basename}")


def _parse_listen(name: str, value: str) -> int:
    _require(" " not in value and ";" not in value, f"{name} contains unsafe characters")
    port_text = value.rsplit(":", 1)[-1]
    _require(port_text.isdigit(), f"{name} must end with a numeric port")
    port = int(port_text)
    _require(1 <= port <= 65535, f"{name} port out of range")
    if ":" in value:
        host = value.rsplit(":", 1)[0]
        _require(
            host in {"*", "127.0.0.1", "[::1]", "[::]"} or re.fullmatch(r"[0-9.]+", host),
            f"{name} host must be a literal address",
        )
    return port


def _memory_bytes(value: str, name: str) -> int:
    _require(bool(MEM_RE.fullmatch(value)), f"{name} must be like 800M")
    unit = value[-1]
    amount = int(value[:-1])
    return amount * {"K": 1024, "M": 1024**2, "G": 1024**3}[unit]


def _domain(value: str) -> None:
    _require(bool(DOMAIN_RE.fullmatch(value)), "SITE_DOMAIN must be a lowercase DNS name")


def validate_config(values: dict[str, str], *, production: bool = False) -> dict[str, str]:
    missing = sorted(REQUIRED_KEYS - values.keys())
    _require(not missing, "missing config keys: " + ", ".join(missing))

    root = _abs_path("DEPLOY_ROOT", values["DEPLOY_ROOT"])
    _require(root not in RESERVED_ROOTS, "DEPLOY_ROOT must be a dedicated directory")
    _require(len(Path(root).parts) >= 3, "DEPLOY_ROOT must be at least /opt/<name>")

    for name in ("SERVICE_NAME", "SERVICE_USER", "SERVICE_GROUP"):
        _require(bool(SERVICE_RE.fullmatch(values[name])), f"{name} is invalid")
    _require(values["SERVICE_USER"] == "aicardhub", "SERVICE_USER must be the dedicated aicardhub user")
    _require(values["SERVICE_GROUP"] == "aicardhub", "SERVICE_GROUP must be the dedicated aicardhub group")
    _require(values["SERVICE_USER"] != values["NGINX_USER"], "service and nginx users must differ")

    releases = _abs_path("RELEASES_DIR", values["RELEASES_DIR"])
    shared = _abs_path("SHARED_DIR", values["SHARED_DIR"])
    uploads = _abs_path("UPLOAD_DIR", values["UPLOAD_DIR"])
    kb = _abs_path("KB_DIR", values["KB_DIR"])
    logs = _abs_path("LOG_DIR", values["LOG_DIR"])
    ops = _abs_path("OPS_DIR", values["OPS_DIR"])
    current = _abs_path("CURRENT_LINK", values["CURRENT_LINK"])
    env_file = _abs_path("ENV_FILE", values["ENV_FILE"])
    gate = _abs_path("MIGRATION_GATE_FILE", values["MIGRATION_GATE_FILE"])
    for name, child in (
        ("RELEASES_DIR", releases),
        ("SHARED_DIR", shared),
        ("LOG_DIR", logs),
        ("OPS_DIR", ops),
        ("CURRENT_LINK", current),
    ):
        _require(_under(child, root), f"{name} must be under DEPLOY_ROOT")
    _require(releases != root and shared != root and logs != root and ops != root, "directory overlap")
    directories = {
        "RELEASES_DIR": releases,
        "SHARED_DIR": shared,
        "LOG_DIR": logs,
        "OPS_DIR": ops,
    }
    for left_name, left in directories.items():
        for right_name, right in directories.items():
            if left_name >= right_name:
                continue
            _require(
                not _under(left, right) and not _under(right, left),
                f"{left_name} and {right_name} must not overlap",
            )
    _require(current == root + "/current", "CURRENT_LINK must be DEPLOY_ROOT/current")
    _exact(env_file, shared, "env", "ENV_FILE")
    _exact(uploads, shared, "uploads", "UPLOAD_DIR")
    _exact(kb, shared, "kb", "KB_DIR")
    _exact(gate, shared, "migration-gate.ok", "MIGRATION_GATE_FILE")
    _require(not _under(env_file, uploads) and not _under(env_file, kb), "ENV_FILE cannot be public")
    _require(not _under(uploads, kb) and not _under(kb, uploads), "uploads and kb must be separate")

    _require(bool(re.fullmatch(r"[A-Za-z0-9._-]{1,64}", values["VENV_DIR"])), "VENV_DIR is invalid")
    _require("/" not in values["VENV_DIR"], "VENV_DIR must be a single relative name")
    _require(values["API_HOST"] == "127.0.0.1", "API_HOST must be exactly 127.0.0.1")
    _require(values["API_PORT"].isdigit(), "API_PORT must be numeric")
    api_port = int(values["API_PORT"])
    _require(1024 <= api_port <= 65535, "API_PORT must be an unprivileged port")
    _require(values["API_WORKERS"] == "1", "API_WORKERS must be exactly 1")
    _require(api_port not in {80, 443, 3306}, "API_PORT collides with a reserved service")

    for name, pattern in (("API_UNIT", UNIT_RE), ("SCHEDULER_UNIT", UNIT_RE), ("BACKUP_UNIT", UNIT_RE)):
        _require(bool(pattern.fullmatch(values[name])), f"{name} must be a .service basename")
    _require(bool(TIMER_RE.fullmatch(values["BACKUP_TIMER"])), "BACKUP_TIMER must be a .timer basename")
    unit_names = [values["API_UNIT"], values["SCHEDULER_UNIT"], values["BACKUP_UNIT"]]
    _require(len(set(unit_names)) == 3, "API, scheduler and backup unit names must differ")
    _require(values["BACKUP_TIMER"] not in unit_names, "BACKUP_TIMER must differ from service names")

    for name in ("API_MEMORY_HIGH", "API_MEMORY_MAX", "SCHEDULER_MEMORY_HIGH", "SCHEDULER_MEMORY_MAX"):
        _memory_bytes(values[name], name)
    _require(
        _memory_bytes(values["API_MEMORY_MAX"], "API_MEMORY_MAX")
        > _memory_bytes(values["API_MEMORY_HIGH"], "API_MEMORY_HIGH"),
        "API_MEMORY_MAX must exceed API_MEMORY_HIGH",
    )
    _require(
        _memory_bytes(values["SCHEDULER_MEMORY_MAX"], "SCHEDULER_MEMORY_MAX")
        > _memory_bytes(values["SCHEDULER_MEMORY_HIGH"], "SCHEDULER_MEMORY_HIGH"),
        "SCHEDULER_MEMORY_MAX must exceed SCHEDULER_MEMORY_HIGH",
    )

    _require(bool(SITE_RE.fullmatch(values["SITE_NAME"])), "SITE_NAME is invalid")
    _domain(values["SITE_DOMAIN"])
    _require(values["STAGE_SERVER_NAME"] == "localhost", "STAGE_SERVER_NAME must be localhost")
    _require(values["STAGE_LISTEN"] == "127.0.0.1:18080", "STAGE_LISTEN must be 127.0.0.1:18080")
    _parse_listen("STAGE_LISTEN", values["STAGE_LISTEN"])
    include_file = _abs_path("NGINX_INCLUDE_FILE", values["NGINX_INCLUDE_FILE"])
    stage_file = _abs_path("STAGE_CONF_FILE", values["STAGE_CONF_FILE"])
    nginx_log = _abs_path("NGINX_LOG_DIR", values["NGINX_LOG_DIR"])
    _require(_under(include_file, ops), "NGINX_INCLUDE_FILE must be under OPS_DIR")
    _require(_under(stage_file, ops), "STAGE_CONF_FILE must be under OPS_DIR")
    _require(include_file != stage_file, "NGINX_INCLUDE_FILE and STAGE_CONF_FILE must differ")
    _require(not _under(include_file, nginx_log), "include file cannot be a log")
    _require(not _under(stage_file, nginx_log), "stage file cannot be a log")

    deploy_lock = _abs_path("DEPLOY_LOCK", values["DEPLOY_LOCK"])
    maintenance_lock = _abs_path("MAINTENANCE_LOCK", values["MAINTENANCE_LOCK"])
    _require(deploy_lock == maintenance_lock, "DEPLOY_LOCK and MAINTENANCE_LOCK must be the same common maintenance lock")
    _require(deploy_lock.startswith("/run/"), "locks must live under /run")

    nginx_pid = _abs_path("NGINX_PID_FILE", values["NGINX_PID_FILE"])
    access = _abs_path("NGINX_ACCESS_LOG", values["NGINX_ACCESS_LOG"])
    error = _abs_path("NGINX_ERROR_LOG", values["NGINX_ERROR_LOG"])
    _require(access != error, "nginx access and error logs must differ")
    _require(_under(access, nginx_log) and _under(error, nginx_log), "nginx logs must be under NGINX_LOG_DIR")
    _require(not _under(nginx_log, root), "nginx logs must not be under the deploy root")
    _require(nginx_pid.endswith("/nginx.pid"), "NGINX_PID_FILE must end with /nginx.pid")
    _require(values["NGINX_USER"] != values["SERVICE_USER"], "nginx and service users must differ")
    _require(bool(SERVICE_RE.fullmatch(values["NGINX_USER"])), "NGINX_USER is invalid")
    _require(bool(SERVICE_RE.fullmatch(values["NGINX_GROUP"])), "NGINX_GROUP is invalid")
    _require(bool(SERVICE_RE.fullmatch(values["NGINX_LOG_GROUP"])), "NGINX_LOG_GROUP is invalid")

    logrotate_dir = _abs_path("LOGROTATE_CONF_DIR", values["LOGROTATE_CONF_DIR"])
    systemd_dir = _abs_path("SYSTEMD_UNIT_DIR", values["SYSTEMD_UNIT_DIR"])
    _require(logrotate_dir not in {root, "/etc"}, "LOGROTATE_CONF_DIR must be a dedicated directory")
    _require(systemd_dir not in {root, "/etc"}, "SYSTEMD_UNIT_DIR must be a dedicated directory")

    backup_root = _abs_path("BACKUP_ROOT", values["BACKUP_ROOT"])
    _require(not _under(backup_root, root), "BACKUP_ROOT must be outside the deploy root")
    _require(not _under(backup_root, nginx_log), "BACKUP_ROOT must be outside web/log roots")
    _require(values["BACKUP_RETENTION_DAYS"].isdigit(), "BACKUP_RETENTION_DAYS must be numeric")
    _require(1 <= int(values["BACKUP_RETENTION_DAYS"]) <= 365, "BACKUP_RETENTION_DAYS out of range")
    backup_log = _abs_path("BACKUP_LOG", values["BACKUP_LOG"])
    _require(_under(backup_log, logs), "BACKUP_LOG must be under LOG_DIR")
    backup_env = _abs_path("BACKUP_ENV_FILE", values["BACKUP_ENV_FILE"])
    mysql_cnf = _abs_path("MYSQL_DEFAULTS_FILE", values["MYSQL_DEFAULTS_FILE"])
    _require(not _under(backup_env, root), "BACKUP_ENV_FILE must be outside the deploy root")
    _require(not _under(mysql_cnf, root), "MYSQL_DEFAULTS_FILE must be outside the deploy root")
    _require(bool(DB_RE.fullmatch(values["MYSQL_DATABASE"])), "MYSQL_DATABASE is invalid")
    _require(bool(re.fullmatch(r"[A-Za-z0-9_./-]{1,128}", values["MYSQL_DUMP_BIN"])), "MYSQL_DUMP_BIN is invalid")
    _require(values["PYTHON_RUNTIME"].startswith("/"), "PYTHON_RUNTIME must be absolute")
    _abs_path("PYTHON_RUNTIME", values["PYTHON_RUNTIME"])

    if production:
        _require(values["SITE_DOMAIN"] not in {"example.invalid", "card.example.invalid"}, "placeholder domain")
        _require(".invalid" not in values["SITE_DOMAIN"], "placeholder domain")
        _require("REPLACE" not in include_file and "REPLACE" not in stage_file, "placeholder include paths")

    return values


def build_context(values: dict[str, str]) -> dict[str, str]:
    context = dict(values)
    context["H5_DIR"] = values["CURRENT_LINK"] + "/apps/h5/dist"
    context["ADMIN_DIR"] = values["CURRENT_LINK"] + "/apps/admin/dist"
    context["BACKUP_SCRIPT"] = values["OPS_DIR"] + "/backup.sh"
    return context


def render_text(template: str, context: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in context:
            raise ConfigError(f"template references unknown key {key}")
        return context[key]

    rendered = TOKEN_RE.sub(replace, template)
    if "@@" in rendered:
        raise ConfigError("unresolved template placeholder")
    if "\r" in rendered:
        raise ConfigError("rendered output contains CR")
    if not rendered.startswith(GENERATED_MARKER):
        raise ConfigError("template is missing the generated-file marker")
    return rendered


def render_to(
    config_path: Path,
    out_dir: Path,
    *,
    production: bool = False,
    template_root: Path | None = None,
) -> dict[str, Path]:
    values = validate_config(load_config(config_path), production=production)
    context = build_context(values)
    templates = template_root or Path(__file__).resolve().parent.parent / "templates"
    outputs = {
        "aicardhub.locations.conf": templates / "nginx" / "aicardhub.locations.conf.in",
        "aicardhub.stage.conf": templates / "nginx" / "aicardhub.stage.conf.in",
        values["API_UNIT"]: templates / "systemd" / "aicardhub-api.service.in",
        values["SCHEDULER_UNIT"]: templates / "systemd" / "aicardhub-scheduler.service.in",
        values["BACKUP_UNIT"]: templates / "systemd" / "aicardhub-backup.service.in",
        values["BACKUP_TIMER"]: templates / "systemd" / "aicardhub-backup.timer.in",
        values["SITE_NAME"] + ".logrotate": templates / "logrotate" / "aicardhub.conf.in",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for name, source in outputs.items():
        if not source.is_file():
            raise ConfigError(f"missing template {source}")
        rendered = render_text(source.read_text(encoding="utf-8"), context)
        target = out_dir / name
        if target.is_symlink():
            raise ConfigError(f"refusing to write through symlink {target}")
        target.write_text(rendered, encoding="utf-8", newline="\n")
        written[name] = target
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render AICardHub native deployment templates")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--production", action="store_true", help="reject placeholder domain/cert values")
    parser.add_argument("--check", action="store_true", help="validate config without writing output")
    args = parser.parse_args(argv)
    try:
        if args.check:
            validate_config(load_config(args.config), production=args.production)
            print("configuration valid")
            return 0
        if args.out is None:
            parser.error("--out is required unless --check is used")
        written = render_to(args.config, args.out, production=args.production)
        for path in written.values():
            print(path)
        return 0
    except ConfigError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
