"""Measure local API/FakeLLM concurrency; not mobile or real-provider capacity."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import statistics
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--users", type=int, default=50, choices=range(1, 101))
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--chat", action="store_true")
    args = parser.parse_args()

    def call(method: str, path: str, payload: dict[str, object] | None = None, token: str = "") -> tuple[int, object]:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        body = json.dumps(payload).encode() if payload is not None else None
        req = Request(args.base_url + path, data=body, headers=headers, method=method)
        try:
            response = urlopen(req, timeout=60)
        except HTTPError as error:
            response = error
        with response:
            raw = response.read().decode("utf-8-sig")
            try:
                content = json.loads(raw)
            except json.JSONDecodeError:
                content = raw
            return response.status, content

    def run_user(index: int) -> dict[str, object]:
        start = time.monotonic()
        try:
            status, content = call("GET", "/api/v1/public/cards/demo")
            if status != 200:
                return {"user": index, "passed": False, "status": status}
            if args.chat:
                status, visitor = call("POST", "/api/v1/public/visitor/init", {})
                if status != 200 or not isinstance(visitor, dict):
                    return {"user": index, "passed": False, "status": status}
                token = str(visitor["visitor_token"])
                status, session = call("POST", "/api/v1/public/chat/sessions", {"card_code": "demo"}, token)
                if status != 200 or not isinstance(session, dict):
                    return {"user": index, "passed": False, "status": status}
                status, content = call("POST", f"/api/v1/public/chat/sessions/{session['session_id']}/messages", {"content": "介绍合成演示资料"}, token)
                passed = status == 200 and isinstance(content, str) and "event: done" in content
            else:
                passed = isinstance(content, dict) and content.get("code") == "demo"
            return {"user": index, "passed": passed, "status": status, "seconds": round(time.monotonic() - start, 4)}
        except Exception as error:
            return {"user": index, "passed": False, "error": type(error).__name__, "seconds": round(time.monotonic() - start, 4)}

    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.users) as pool:
        results = list(pool.map(run_user, range(args.users)))
    durations = sorted(float(item["seconds"]) for item in results if "seconds" in item)
    report = {
        "scenario": "50 local clients, each card+visitor+session+SSE" if args.chat else "local concurrent card reads",
        "limitations": "localhost desktop network; chat only meaningful as FakeLLM capacity unless separately configured; not 4G, NFC or real-model throughput",
        "concurrency": args.users,
        "passed": sum(bool(item["passed"]) for item in results),
        "failed": sum(not item["passed"] for item in results),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "median_seconds": statistics.median(durations) if durations else None,
        "p95_seconds": durations[max(0, int(len(durations) * 0.95) - 1)] if durations else None,
        "results": results,
    }
    root = Path(__file__).resolve().parents[1]
    output = root / "tasks/reports" / ("local-load-chat.json" if args.chat else "local-load-card.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "results"}, ensure_ascii=False))
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
