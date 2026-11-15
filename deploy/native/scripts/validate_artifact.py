#!/usr/bin/env python3
"""Validate a prebuilt AICardHub release directory or tar archive.

Rejects absolute/escaping symlinks, symlink-descendant writes, hardlinks in tar,
special files, setuid/setgid bits, product env files and bundled credentials.
This is a release-validation tool; it never executes release code.
"""

from __future__ import annotations

import argparse
import os
import posixpath
import stat
import subprocess
import sys
import tarfile
from pathlib import Path

REQUIRED = (
    "server/app/main.py",
    "server/app/scheduler.py",
    "server/alembic.ini",
    "server/alembic",
    "server/uv.lock",
    "server/pyproject.toml",
    "apps/h5/dist/index.html",
    "apps/h5/dist/assets",
    "apps/admin/dist/index.html",
    "apps/admin/dist/assets",
    "venv/bin/python",
    "venv/pyvenv.cfg",
)

# A standard `uv venv` records an absolute symlink to the interpreter. The
# deployment package intentionally does not install dependencies or rebuild the
# venv on the host, so this one link may point at an explicitly validated system
# Python 3.12 target. Every other absolute symlink remains forbidden.
ALLOWED_SYSTEM_PYTHON = {
    "/usr/bin/python3.12",
    "/usr/local/bin/python3.12",
    "/bin/python3.12",
}


class ArtifactError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ArtifactError(message)


def normalize(name: str) -> str:
    require(bool(name), "empty archive path")
    require("\\" not in name, f"backslash in path: {name}")
    require(not name.startswith("/"), f"absolute path: {name}")
    require(not name.startswith("../"), f"escaping path: {name}")
    normalized = posixpath.normpath(name)
    require(normalized not in ("", ".", ".."), f"invalid path: {name}")
    require(not normalized.startswith("../"), f"escaping path: {name}")
    require("/../" not in normalized, f"escaping path: {name}")
    return normalized


def forbidden(name: str) -> str | None:
    parts = name.split("/")
    for part in parts:
        if part in {".git", "node_modules"}:
            return part
        if part == ".env" or part.startswith(".env."):
            return ".env"
        if part == "local-credentials.json":
            return part
        if part.endswith(".credentials.local.json"):
            return part
        if part in {"data.sqlite", "data.sqlite3", "data.db"} or part.endswith(".sqlite"):
            return part
    return None


def present(names: set[str], required: str) -> bool:
    return required in names or any(name.startswith(required.rstrip("/") + "/") for name in names)


def check_required(names: set[str]) -> None:
    missing = [name for name in REQUIRED if not present(names, name)]
    require(not missing, "release missing required paths: " + ", ".join(missing))


def safe_link_target(member_name: str, target: str, names: set[str]) -> None:
    if target.startswith("/"):
        require(
            member_name == "venv/bin/python" and target in ALLOWED_SYSTEM_PYTHON,
            f"absolute symlink target not allowed: {member_name} -> {target}",
        )
        return
    require("\\" not in target, f"backslash symlink target: {member_name} -> {target}")
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(member_name), target))
    require(not resolved.startswith("../") and resolved != "..", f"escaping symlink: {member_name} -> {target}")
    require(present(names, resolved), f"dangling symlink: {member_name} -> {target}")


def check_mode(mode: int, label: str) -> None:
    require((mode & 0o6000) == 0, f"setuid/setgid bit on {label}")


def validate_tar(path: Path) -> tuple[int, set[str]]:
    names: set[str] = set()
    symlinks: dict[str, str] = {}
    with tarfile.open(path, mode="r:*") as archive:
        members = archive.getmembers()
        for member in members:
            name = normalize(member.name)
            require(name not in names, f"duplicate tar entry: {name}")
            names.add(name)
            require(forbidden(name) is None, f"forbidden path in release: {name}")
            check_mode(member.mode, name)
            if member.isdir():
                continue
            if member.issym():
                symlinks[name] = member.linkname
                continue
            require(not member.islnk(), f"hardlink not allowed: {name}")
            require(member.isfile(), f"special file not allowed: {name}")
        for name, target in symlinks.items():
            safe_link_target(name, target, names)
        for name in names:
            for link in symlinks:
                require(not (name != link and name.startswith(link + "/")), f"entry below symlink: {name}")
    check_required(names)
    return len(names), names


def validate_dir(root: Path) -> tuple[int, set[str]]:
    require(root.is_dir(), f"not a directory: {root}")
    require(not root.is_symlink(), f"artifact root must not be a symlink: {root}")
    resolved_root = root.resolve()
    names: set[str] = set()
    symlinks: dict[str, str] = {}
    for current, dirs, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        for name in dirs + files:
            path = current_path / name
            rel = path.relative_to(root).as_posix()
            rel = normalize(rel)
            names.add(rel)
            require(forbidden(rel) is None, f"forbidden path in release: {rel}")
            info = path.lstat()
            check_mode(info.st_mode, rel)
            if stat.S_ISLNK(info.st_mode):
                target = os.readlink(path)
                symlinks[rel] = target
                if target.startswith("/"):
                    require(
                        rel == "venv/bin/python" and target in ALLOWED_SYSTEM_PYTHON,
                        f"absolute symlink target not allowed: {rel} -> {target}",
                    )
                    resolved_python = Path(target)
                    require(resolved_python.is_file(), f"system Python link target missing: {target}")
                    require(os.access(resolved_python, os.X_OK), f"system Python link target is not executable: {target}")
                    try:
                        subprocess.run(
                            [str(resolved_python), "-c", "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)"],
                            check=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                    except (OSError, subprocess.CalledProcessError) as exc:
                        raise ArtifactError(f"system Python link is not a validated 3.12 runtime: {target}") from exc
                    continue
                require("\\" not in target, f"backslash symlink target: {rel} -> {target}")
                resolved = (path.parent / target).resolve()
                require(
                    resolved == resolved_root or resolved_root in resolved.parents,
                    f"escaping symlink: {rel} -> {target}",
                )
                require(resolved.exists(), f"dangling symlink: {rel} -> {target}")
            elif stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode):
                continue
            else:
                raise ArtifactError(f"special file not allowed: {rel}")
    for name in names:
        for link in symlinks:
            require(not (name != link and name.startswith(link + "/")), f"entry below symlink: {name}")
    check_required(names)
    return len(names), names


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an AICardHub prebuilt release")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--archive", type=Path)
    group.add_argument("--dir", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.archive:
            count, _ = validate_tar(args.archive)
            print(f"archive valid: {args.archive} ({count} entries)")
        else:
            count, _ = validate_dir(args.dir)
            print(f"directory valid: {args.dir} ({count} entries)")
        return 0
    except (ArtifactError, OSError, tarfile.TarError) as exc:
        print(f"artifact invalid: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
