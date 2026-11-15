"""Server-bound, bounded read-only knowledge capabilities."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger

from app.kb.prompt import public_card_context
from app.kb.store import KnowledgeStore


def _definition(name: str, description: str, arg: str | None) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {arg: {"type": "string"}} if arg else {},
                "required": [arg] if arg else [],
                "additionalProperties": False,
            },
        },
    }


class ToolRuntime:
    definitions = [
        _definition(
            "list_public_knowledge",
            "Discover available knowledge by file_id, title and description; metadata only, at most 64 entries. Use search for more.",
            None,
        ),
        _definition(
            "search_public_knowledge",
            "Search available knowledge for this card; returns bounded excerpts and source IDs",
            "query",
        ),
        _definition(
            "read_public_knowledge",
            "Read an available current document by file_id selected from the directory",
            "file_id",
        ),
        _definition(
            "get_public_card",
            "Read current visitor-visible card and public contact information",
            None,
        ),
    ]

    def __init__(
        self,
        store: KnowledgeStore | None,
        card_code: str,
        *,
        public_card: dict[str, Any] | None = None,
        card_reader: Callable[[], Awaitable[dict[str, Any]]] | None = None,
        preview: bool = False,
    ):
        # preview is set only after employee/session ownership validation, never model input.
        self.store, self.card_code, self.preview = store, card_code, preview
        self.card = public_card_context(public_card)
        self.card_reader = card_reader
        self.refs: list[str] = []
        self.count = 0
        self.committed = False

    def _allowed(self, doc: dict[str, Any] | None) -> bool:
        if not doc or doc.get("deleted", False) is not False:
            return False
        own = doc.get("scope") in {"card", "personal"} and doc.get("card_code") == self.card_code
        if self.preview and own:
            return True
        return bool(
            (doc.get("scope") == "company" or own)
            and doc.get("public") is True
            and doc.get("approved") is True
            and not str(doc.get("file_id", "")).startswith(("profile-", "persona-"))
        )

    def _documents(self, name: str, value: str) -> list[dict[str, Any]]:
        if self.store is None:
            return []
        if name == "read_public_knowledge":
            candidates = [{"file_id": value}]
        elif name == "list_public_knowledge" or self.preview:
            candidates = sorted(
                self.store.list_files(),
                key=lambda doc: (
                    not str(doc["file_id"]).startswith("corrections-"),
                    doc["file_id"],
                ),
            )
        else:
            candidates = self.store.search(value, card_code=self.card_code)
        result: list[dict[str, Any]] = []
        budget = 12000 if name == "list_public_knowledge" else 8000
        for candidate in candidates:
            doc = self.store.get(candidate["file_id"])
            if not self._allowed(doc):
                continue
            assert doc is not None
            if (
                name == "search_public_knowledge"
                and self.preview
                and value.lower()
                not in (doc["title"] + doc.get("description", "") + doc["content"]).lower()
            ):
                continue
            item = {
                "file_id": doc["file_id"],
                "title": doc["title"][:200],
                "description": doc.get("description", "")[:300],
                "scope": doc["scope"],
                "revision": doc.get("revision"),
                "hash": doc.get("hash"),
                "preview": not (doc.get("public") is True and doc.get("approved") is True),
            }
            if name != "list_public_knowledge":
                item["content"] = doc["content"][
                    : 1500 if name == "search_public_knowledge" else 6500
                ]
            size = len(json.dumps(item, ensure_ascii=False))
            if size > budget:
                break
            budget -= size
            result.append(item)
            if len(result) >= (64 if name == "list_public_knowledge" else 3):
                break
        return result

    async def invoke(self, name: str, arguments: str) -> dict[str, Any]:
        self.count += 1
        self.committed = True
        safe_name = name if name in {d["function"]["name"] for d in self.definitions} else "unknown"
        refs: list[str] = []
        rows = 0
        ok = False
        try:
            if self.count > 8:
                return {"ok": False, "error": "tool_budget_exhausted"}
            if safe_name == "unknown":
                return {"ok": False, "error": "unknown_tool"}
            if not isinstance(arguments, str) or len(arguments.encode("utf-8")) > 4096:
                return {"ok": False, "error": "arguments_too_large"}
            args = json.loads(arguments)
            arg = {"search_public_knowledge": "query", "read_public_knowledge": "file_id"}.get(name)
            if not isinstance(args, dict) or set(args) != ({arg} if arg else set()):
                return {"ok": False, "error": "invalid_arguments"}
            if arg and (not isinstance(args[arg], str) or not args[arg].strip()):
                return {"ok": False, "error": "invalid_arguments"}
            if name != "get_public_card":
                docs = await asyncio.to_thread(self._documents, name, args[arg] if arg else "")
                if name == "read_public_knowledge" and not docs:
                    return {"ok": False, "error": "document_unavailable"}
                result = {"ok": True, "documents": docs}
                rows = len(docs)
                if name != "list_public_knowledge":
                    refs = [d["file_id"] for d in docs]
                    self.refs.extend(r for r in refs if r not in self.refs)
            else:
                card = await self.card_reader() if self.card_reader else self.card
                if not card:
                    return {"ok": False, "error": "card_unavailable"}
                result = {"ok": True, "public_card": public_card_context(card)}
                rows = 1
            ok = True
            return result
        except Exception:  # noqa: BLE001 - do not expose database/storage/provider exceptions
            return {"ok": False, "error": "tool_failed"}
        finally:
            logger.info(
                "assistant_tool name={} count={} result_count={} ok={} refs={}",
                safe_name,
                self.count,
                rows,
                ok,
                refs,
            )
            logging.getLogger(__name__).info(
                "tool name=%s count=%d result_count=%d refs=%s", safe_name, self.count, rows, refs
            )
