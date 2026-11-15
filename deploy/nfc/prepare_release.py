"""Prepare local APK metadata and merged Android App Links; never deploy."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit


def validated_base(value: str) -> str:
    parsed = urlsplit(value)
    # Match the APK's build-time origin/path allowlist. Accessing port also
    # rejects non-numeric values such as ':bad', which hostname alone accepts.
    port = parsed.port
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or port is not None
        or ":" in parsed.netloc
        or parsed.query
        or parsed.fragment
        or re.search(r"%|\\|\s", value)
        or any(part in {".", ".."} for part in parsed.path.split("/"))
        or "//" in parsed.path
        or not re.fullmatch(r"(?:/[A-Za-z0-9_-]+)*/?", parsed.path)
    ):
        raise ValueError("public base must be an HTTPS origin with an optional deployment path")
    return value.rstrip("/")


def fingerprint(value: str) -> str:
    compact = value.replace(":", "").upper()
    if not re.fullmatch(r"[0-9A-F]{64}", compact):
        raise ValueError("certificate fingerprint must contain exactly 32 SHA-256 bytes")
    return ":".join(compact[index : index + 2] for index in range(0, 64, 2))


def merged_links(existing: object, package: str, certificate: str) -> list[object]:
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+", package):
        raise ValueError("invalid Android application id")
    if not isinstance(existing, list):
        raise TypeError("existing assetlinks.json must be a JSON array")
    entry = {
        "relation": ["delegate_permission/common.handle_all_urls"],
        "target": {
            "namespace": "android_app",
            "package_name": package,
            "sha256_cert_fingerprints": [fingerprint(certificate)],
        },
    }
    # Preserve existing applications, relations and signing certificates intact.
    return existing if entry in existing else [*existing, entry]


def prepare(args: argparse.Namespace) -> None:
    base = validated_base(args.public_base_url)
    apk = args.apk.resolve(strict=True)
    if apk.suffix.lower() != ".apk" or not apk.is_file():
        raise ValueError("apk must reference an existing .apk file")
    existing = json.loads(args.existing_assetlinks.read_text("utf-8")) if args.existing_assetlinks else []
    links = merged_links(existing, args.package_id, args.certificate_sha256)
    output = args.output_dir.resolve()
    if output.exists():
        raise ValueError("output directory must be new; existing release files are never overwritten")
    raw = apk.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    apk_name = f"aicardhub-nfc-{digest[:12]}.apk"
    output.mkdir(parents=True)
    (output / apk_name).write_bytes(raw)
    (output / "assetlinks.json").write_text(json.dumps(links, indent=2) + "\n", "utf-8")
    manifest = {
        "public_base_url": base,
        "application_id": args.package_id,
        "certificate_sha256": fingerprint(args.certificate_sha256),
        "apk": apk_name,
        "sha256": digest,
        "bytes": len(raw),
        "channel": args.channel,
        "app_link_path": f"{urlsplit(base).path}/share/nfc",
        "assetlinks_location": "/.well-known/assetlinks.json",
        "deployment_status": "prepared_locally",
        "device_acceptance": "not_asserted_by_this_tool",
    }
    (output / "release.json").write_text(json.dumps(manifest, indent=2) + "\n", "utf-8")
    print(json.dumps({"output": str(output), "apk_sha256": digest, "channel": args.channel}))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apk", required=True, type=Path)
    parser.add_argument("--package-id", required=True)
    parser.add_argument("--certificate-sha256", required=True)
    parser.add_argument("--public-base-url", required=True)
    parser.add_argument("--existing-assetlinks", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--channel", choices=["debug-test", "release"], default="debug-test")
    args = parser.parse_args()
    try:
        prepare(args)
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(2, f"Cannot prepare NFC release: {exc}\n")


if __name__ == "__main__":
    main()
