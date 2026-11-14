"""Validate exported API operation identities and minimum local delivery surface."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "/api/v1/auth/login": {"post"},
    "/api/v1/admin/auth/login": {"post"},
    "/api/v1/auth/change-password": {"post"},
    "/api/v1/me/profile": {"get"},
    "/api/v1/public/visitor/init": {"post"},
    "/api/v1/public/cards/{code}": {"get"},
    "/api/v1/public/cards/{code}/vcard": {"get"},
    "/api/v1/public/leads": {"post"},
    "/api/v1/public/chat/sessions": {"post"},
    "/api/v1/public/chat/sessions/{session_id}/messages": {"get", "post"},
    "/api/v1/me/card": {"get", "put"},
    "/api/v1/me/card/share": {"get"},
    "/api/v1/me/assistant": {"get", "put"},
    "/api/v1/me/leads": {"get"},
    "/api/v1/me/stats": {"get"},
    "/api/v1/me/kb/notes": {"get", "post"},
    "/api/v1/admin/company": {"get", "put"},
    "/api/v1/admin/employees": {"get", "post"},
    "/api/v1/admin/templates": {"get", "post"},
    "/api/v1/admin/kb/files": {"get", "post"},
}
METHODS = {"get", "put", "post", "delete", "patch", "options", "head"}


def normalized(path: str) -> str:
    import re

    return re.sub(r"\{[^}]+\}", "{}", path)


def main() -> int:
    source = ROOT / "contracts/openapi.json"
    raw = source.read_bytes()
    schema = json.loads(raw)
    paths = schema["paths"]
    issues: list[str] = []
    identifiers: set[str] = set()
    operations = 0
    normalized_paths = {normalized(path): value for path, value in paths.items()}
    for path, methods in REQUIRED.items():
        actual = normalized_paths.get(normalized(path), {})
        for method in methods:
            if method not in actual:
                issues.append(f"Missing {method.upper()} {path}")
    for path, item in paths.items():
        for method, operation in item.items():
            if method not in METHODS:
                continue
            operations += 1
            operation_id = operation.get("operationId")
            if not operation_id or operation_id in identifiers:
                issues.append(f"Missing/duplicate operationId: {method} {path}")
            identifiers.add(operation_id)
            successes = {
                str(status): data
                for status, data in operation.get("responses", {}).items()
                if str(status).startswith("2")
            }
            if not successes and path != "/c/{code}":
                issues.append(f"No documented success response: {method} {path}")
    report = {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "operations": operations,
        "issues": issues,
        "passed": not issues,
    }
    output = ROOT / "tasks/reports/contract-check.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
