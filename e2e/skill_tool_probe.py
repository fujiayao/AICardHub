"""Manual real-provider probe; no data mutations, never prints credentials/raw logs."""

import asyncio
import json
import os
from pathlib import Path
import re
import sys

from loguru import logger

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))


async def main():
    if os.environ.get("AICARD_REAL_AI_CHECK") != "1":
        raise RuntimeError("Explicit real-model opt-in required")
    from app.core.db import SessionLocal, engine
    from app.integrations.llm import ChatEngine
    from app.kb.tools import ToolRuntime
    from app.modules.workspace.knowledge_service import get_store
    from app.modules.workspace.runtime_settings import clients, close_client, load
    from app.modules.workspace.service import public_card

    calls = []

    def audit(message):
        match = re.search(
            r"assistant_tool name=([a-z_]+) count=(\d+) result_count=(\d+) ok=(True|False)",
            message.record["message"],
        )
        if match:
            calls.append({"name": match[1], "count": int(match[2]),
                          "result_count": int(match[3]), "ok": match[4] == "True"})

    sink = logger.add(audit, filter=lambda record: record["name"] == "app.kb.tools")
    primary = None
    backups = []
    report = {"tools": calls, "read_only": True}
    try:
        async with SessionLocal() as db:
            settings = await load(db)
            card = await public_card(db, "5dbb1d43")
        primary, backups = clients(settings)
        runtime = ToolRuntime(await get_store(), card.code, public_card=card.model_dump())
        identity = {"name": card.name, "title": card.title,
                    "company": {"name": card.company.name, "short_name": card.company.short_name}}
        events = [event async for event in ChatEngine(primary, fallbacks=backups).stream(
            "请调用知识库，先看目录简介，再读相关文档，概括义乌数科的已公开业务方向。", [], [],
            public_card=identity, tools=runtime,
        )]
        report["answer"] = "".join(event["data"]["text"] for event in events if event["event"] == "delta")
        report["done"] = next((event["data"] for event in events if event["event"] == "done"), None)
        report["errors"] = [event["data"] for event in events if event["event"] == "error"]
        report["passed"] = bool(report["done"] and not report["errors"]
            and any(c["name"] == "list_public_knowledge" and c["ok"] for c in calls)
            and any(c["name"] == "read_public_knowledge" and c["ok"] and c["result_count"] for c in calls))
    finally:
        for client in [primary, *backups]:
            await close_client(client)
        await engine.dispose()
        logger.remove(sink)
        out = ROOT / "tasks/reports/skill-assistant/native-tool-probe.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": report.get("passed", False), "tools": calls}, ensure_ascii=False))
    if not report.get("passed"):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
