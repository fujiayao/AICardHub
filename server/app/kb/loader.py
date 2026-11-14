"""Parse knowledge text without filesystem access or sending drafts to a model."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from functools import lru_cache
from typing import Any

import frontmatter
import tiktoken
from yaml import YAMLError

logger = logging.getLogger(__name__)
MAX_DOCUMENT_CHARS = 100_000
SCOPES = frozenset({"company", "card", "personal"})
_RESERVED = frozenset({"con", "prn", "aux", "nul", "clock$", "conin$", "conout$"})


def validate_id(value: str) -> str:
    """Accept portable opaque IDs, never paths, extensions or Windows devices."""
    if (
        not isinstance(value, str)
        or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,99}", value)
        or value in _RESERVED
        or re.fullmatch(r"(?:com|lpt)[0-9]", value)
    ):
        raise ValueError("Invalid knowledge ID")
    return value


def validate_scope(scope: str, card_code: str | None) -> None:
    if scope not in SCOPES:
        raise ValueError("Unknown knowledge scope")
    if scope == "company":
        if card_code is not None:
            raise ValueError("Company knowledge cannot belong to a card")
    elif card_code is None:
        raise ValueError("Card knowledge requires card_code")
    else:
        validate_id(card_code)


@lru_cache(maxsize=1)
def _encoding() -> Any:
    try:
        return tiktoken.get_encoding("o200k_base")
    except Exception:  # noqa: BLE001 - tokenizer/cache/network failures all use the documented fallback
        logger.warning("Tokenizer unavailable; using conservative character estimate")
        return None


def estimate_tokens(text: str) -> int:
    encoding = _encoding()
    if encoding is not None:
        return len(encoding.encode(text, disallowed_special=()))
    chinese = len(re.findall(r"[\u3400-\u9fff]", text))
    words = len(re.findall(r"[A-Za-z0-9_]+", text))
    other = len(re.sub(r"[\u3400-\u9fffA-Za-z0-9_\s]", "", text))
    return math.ceil(chinese + words * 1.3 + other)


def bounded_text(text: str, tokens: int, *, chars: int = 12_000) -> str:
    """Bound both estimated tokens and characters, including tokenizer fallback."""
    text = text[:chars]
    if estimate_tokens(text) <= tokens:
        return text
    low, high = 0, len(text)
    while low < high:
        middle = (low + high + 1) // 2
        if estimate_tokens(text[:middle]) <= tokens:
            low = middle
        else:
            high = middle - 1
    return text[:low]


def document_hash(document: dict[str, Any]) -> str:
    payload = {
        key: value for key, value in document.items() if key not in {"hash", "tokens"}
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha1(encoded.encode("utf-8")).hexdigest()


def parse_document(text: str, file_id: str) -> dict[str, Any]:
    """Parse and validate one stored Markdown revision; invalid documents fail closed."""
    validate_id(file_id)
    if len(text) > MAX_DOCUMENT_CHARS + 8_000:
        raise ValueError("Knowledge document too large")
    try:
        post = frontmatter.loads(text)
    except YAMLError as exc:
        raise ValueError("Invalid knowledge frontmatter") from exc
    metadata: dict[str, Any] = dict(post.metadata)
    if metadata.get("file_id", metadata.get("id", file_id)) != file_id:
        raise ValueError("Knowledge ID differs from filename")
    title = metadata.get("title")
    if not title:
        heading = re.search(r"^#\s+(.+)$", post.content, re.MULTILINE)
        title = heading.group(1).strip() if heading else file_id
    if not isinstance(title, str) or not title.strip() or len(title) > 300:
        raise ValueError("Invalid knowledge title")
    scope, card_code = metadata.get("scope", "company"), metadata.get("card_code")
    validate_scope(scope, card_code)
    for flag in ("public", "approved", "deleted"):
        if type(metadata.get(flag, False)) is not bool:
            raise ValueError(f"Invalid {flag} flag")
    revision = metadata.get("revision", 1)
    if type(revision) is not int or revision < 1:
        raise ValueError("Invalid revision")
    description = metadata.get("description", "")
    if not isinstance(description, str) or len(description) > 1000:
        raise ValueError("Invalid description")
    document: dict[str, Any] = {
        "file_id": file_id,
        "title": title.strip(),
        "content": post.content,
        "description": description,
        "scope": scope,
        "card_code": card_code,
        "public": metadata.get("public", False),
        "approved": metadata.get("approved", False),
        "deleted": metadata.get("deleted", False),
        "revision": revision,
        "updated": str(metadata.get("updated", "")),
    }
    digest = document_hash(document)
    if "hash" in metadata and metadata["hash"] != digest:
        raise ValueError("Knowledge revision hash mismatch")
    document["hash"] = digest
    document["tokens"] = estimate_tokens(document["content"])
    return document


def serialize_document(document: dict[str, Any]) -> str:
    metadata = {
        key: value
        for key, value in document.items()
        if key not in {"content", "tokens"}
    }
    return frontmatter.dumps(frontmatter.Post(document["content"], **metadata)) + "\n"
