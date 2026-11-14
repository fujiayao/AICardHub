"""Read-only, loopback-only metadata check. No model generation or credentials."""
from __future__ import annotations
import argparse
import datetime as dt
import http.client
import json
from pathlib import Path
from urllib.parse import urlsplit

MAX_BYTES = 1_048_576

def check(base_url: str) -> dict:
    u = urlsplit(base_url)
    if (u.scheme != "http" or u.hostname not in {"127.0.0.1", "localhost", "::1"}
            or u.username or u.password or u.query or u.fragment or u.path not in {"", "/"}):
        raise ValueError("Only a plain loopback HTTP origin is accepted")
    result = {"checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
              "origin": base_url.rstrip("/"), "evidence_level": "metadata_only", "requests": {}}
    for endpoint in ("/health", "/v1/models"):
        conn = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=5)
        record: dict = {}
        try:
            conn.request("GET", endpoint, headers={"Accept": "application/json"})
            response = conn.getresponse()
            record["status"] = response.status
            data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                record["error"] = "response_too_large"
            elif response.status == 200 and endpoint == "/v1/models":
                parsed = json.loads(data)
                models = parsed.get("data") if isinstance(parsed, dict) else None
                if not isinstance(models, list):
                    record["error"] = "unexpected_models_schema"
                else:
                    record["model_count"] = len(models)
                    families = {"gpt": 0, "claude": 0, "deepseek": 0, "other": 0}
                    for item in models:
                        mid = str(item.get("id", "")).lower() if isinstance(item, dict) else ""
                        family = next((f for f in ("deepseek", "claude", "gpt") if f in mid), "other")
                        families[family] += 1
                    record["id_family_hints"] = families
                    record["note"] = "ID strings only; no generation, permissions, tools or vendor availability proven"
        except (OSError, ValueError, http.client.HTTPException) as exc:
            record["error_type"] = type(exc).__name__
        finally:
            conn.close()
        result["requests"][endpoint] = record
    return result

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:3425")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = check(args.base_url)
    except ValueError:
        parser.error("Use a loopback-only origin without credentials or URL suffixes")
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        if args.output.exists():
            parser.error("Output already exists; choose a new evidence file")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as out:
            out.write(text + "\n")
    print(text)
    models = result["requests"]["/v1/models"]
    return 0 if models.get("status") == 200 and "error" not in models and "error_type" not in models else 1

if __name__ == "__main__":
    raise SystemExit(main())
