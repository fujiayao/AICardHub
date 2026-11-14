"""The sole filesystem entry point for knowledge, revisions and local Git history.

All public methods are synchronous. Use a thread pool from async application code.
IDs are globally unique and their scope/owner cannot be changed after creation.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import subprocess
import uuid
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from filelock import FileLock

from app.kb.loader import (
    MAX_DOCUMENT_CHARS,
    bounded_text,
    document_hash,
    estimate_tokens,
    parse_document,
    serialize_document,
    validate_id,
    validate_scope,
)

logger = logging.getLogger(__name__)


class KnowledgeStore:
    """A process-safe, revisioned Markdown store with fail-closed public search."""

    def __init__(self, root: str | Path):
        self.root = Path(root).absolute()
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink() or self.root.is_junction():
            raise ValueError("Knowledge root cannot be a link")
        self.root = self.root.resolve()
        lock_path = self._safe(self.root / ".store.lock")
        # A contending worker may wait behind several Windows Git commits.
        # Keep acquisition bounded without timing out a healthy short write queue.
        self._lock = FileLock(str(lock_path), timeout=120)
        self._cache: dict[str, tuple[str, dict[str, Any]]] = {}
        with self._lock:
            git_dir = self._safe(self.root / ".git")
            if not git_dir.exists():
                self._git("init", "--quiet")
            elif not git_dir.is_dir():
                raise ValueError("Knowledge Git directory must be local")

    def _safe(self, path: Path) -> Path:
        """Reject traversal, symlinks and Windows junctions before touching a path."""
        try:
            relative = path.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("Path outside knowledge root") from exc
        current = self.root
        for part in relative.parts:
            if part in {".", ".."}:
                raise ValueError("Invalid knowledge path")
            current = current / part
            if current.is_symlink() or current.is_junction():
                raise ValueError("Knowledge paths cannot contain links")
        if not path.resolve().is_relative_to(self.root):
            raise ValueError("Path outside knowledge root")
        return path

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "-c",
                "core.hooksPath=",
                "-c",
                "commit.gpgsign=false",
                "-c",
                "user.name=Knowledge Store",
                "-c",
                "user.email=knowledge@localhost",
                *args,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.strip()

    def _path(self, file_id: str, scope: str, card_code: str | None) -> Path:
        validate_id(file_id)
        validate_scope(scope, card_code)
        directory = (
            self.root / "company"
            if scope == "company"
            else (self.root / "cards" / str(card_code) / "notes")
        )
        return self._safe(directory / f"{file_id}.md")

    def _paths(self) -> list[Path]:
        paths: list[Path] = []
        company = self._safe(self.root / "company")
        if company.exists():
            paths.extend(self._safe(path) for path in company.glob("*.md"))
        cards = self._safe(self.root / "cards")
        if cards.exists():
            for card in cards.iterdir():
                self._safe(card)
                if not card.is_dir():
                    continue
                validate_id(card.name)
                notes = self._safe(card / "notes")
                if notes.exists():
                    paths.extend(self._safe(path) for path in notes.glob("*.md"))
        return sorted(paths)

    def _read(self, path: Path) -> dict[str, Any]:
        self._safe(path)
        if path.stat().st_size > 4 * (MAX_DOCUMENT_CHARS + 8000):
            raise ValueError("Knowledge document too large")
        raw = path.read_text(encoding="utf-8")
        digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()
        key = str(path)
        if key not in self._cache or self._cache[key][0] != digest:
            document = parse_document(raw, path.stem)
            expected = self._path(document["file_id"], document["scope"], document["card_code"])
            if path != expected:
                raise ValueError("Knowledge owner differs from path")
            if len(self._cache) >= 256:
                self._cache.clear()
            self._cache[key] = digest, document
        return deepcopy(self._cache[key][1])

    def _get(self, file_id: str) -> dict[str, Any] | None:
        matches = [path for path in self._paths() if path.stem == file_id]
        if len(matches) > 1:
            raise ValueError("Duplicate knowledge ID")
        return self._read(matches[0]) if matches else None

    def _history(self, file_id: str) -> list[dict[str, Any]]:
        directory = self._safe(self.root / ".history" / file_id)
        if not directory.exists():
            return []
        documents = []
        for path in directory.glob("*.md"):
            self._safe(path)
            if not path.stem.isdecimal():
                raise ValueError("Invalid revision filename")
            document = parse_document(path.read_text(encoding="utf-8"), file_id)
            if document["revision"] != int(path.stem):
                raise ValueError("Revision differs from filename")
            documents.append(document)
        return sorted(documents, key=lambda document: document["revision"], reverse=True)

    def _atomic_write(self, path: Path, text: str) -> None:
        self._safe(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._safe(path.with_name(f".{uuid.uuid4().hex}.tmp"))
        try:
            with temporary.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def _save(self, document: dict[str, Any]) -> dict[str, Any]:
        path = self._path(document["file_id"], document["scope"], document["card_code"])
        snapshot = self._safe(
            self.root / ".history" / document["file_id"] / f"{document['revision']}.md"
        )
        if snapshot.exists():
            raise ValueError("Revision already exists")
        document["updated"] = datetime.now(UTC).isoformat()
        document["hash"] = document_hash(document)
        text = serialize_document(document)
        # Validate serialized text before it can become a current revision.
        result = parse_document(text, document["file_id"])
        previous = path.read_text(encoding="utf-8") if path.exists() else None
        paths = [str(path.relative_to(self.root)), str(snapshot.relative_to(self.root))]
        try:
            self._atomic_write(snapshot, text)
            if document["deleted"]:
                path.unlink(missing_ok=True)
            else:
                self._atomic_write(path, text)
            # On a first write followed by deletion, path is already Git-tracked.
            self._git("add", "--", *paths)
            self._git(
                "commit",
                "--quiet",
                "-m",
                f"kb: {document['file_id']} r{document['revision']}",
                "--",
                *paths,
            )
        except Exception:
            snapshot.unlink(missing_ok=True)
            if previous is None:
                path.unlink(missing_ok=True)
            else:
                self._atomic_write(path, previous)
            # Restore only our index entries; never reset a caller's repository.
            try:
                self._git("reset", "--quiet", "--", *paths)
            except subprocess.CalledProcessError:
                self._git("rm", "--cached", "--ignore-unmatch", "--", *paths)
            raise
        self._cache.clear()
        return result

    def upsert(
        self,
        file_id: str,
        title: str,
        content: str,
        *,
        public: bool = False,
        approved: bool = False,
        scope: str = "company",
        card_code: str | None = None,
    ) -> dict[str, Any]:
        validate_id(file_id)
        validate_scope(scope, card_code)
        if not isinstance(title, str) or not title.strip() or len(title) > 300:
            raise ValueError("Invalid knowledge title")
        if not isinstance(content, str) or len(content) > MAX_DOCUMENT_CHARS:
            raise ValueError("Invalid knowledge content")
        if type(public) is not bool or type(approved) is not bool:
            raise ValueError("Publication flags must be booleans")
        with self._lock:
            versions = self._history(file_id)
            current = self._get(file_id)
            previous = current or (versions[0] if versions else None)
            if previous and (previous["scope"], previous["card_code"]) != (
                scope,
                card_code,
            ):
                raise ValueError("Knowledge scope and card are immutable")
            # Markdown body is canonicalized by frontmatter; hash its exact stored representation.
            document = {
                "file_id": file_id,
                "title": title.strip(),
                "content": content.strip(),
                "description": "",
                "scope": scope,
                "card_code": card_code,
                "public": public,
                "approved": approved,
                "deleted": False,
                "revision": max(
                    current["revision"] if current else 0,
                    versions[0]["revision"] if versions else 0,
                )
                + 1,
            }
            return self._save(document)

    def list_files(
        self, scope: str | None = None, card_code: str | None = None
    ) -> list[dict[str, Any]]:
        if scope is not None and scope not in {"company", "card", "personal"}:
            raise ValueError("Unknown knowledge scope")
        if card_code is not None:
            validate_id(card_code)
        with self._lock:
            documents = []
            for path in self._paths():
                try:
                    document = self._read(path)
                except (ValueError, TypeError, UnicodeError):
                    logger.warning("Excluded invalid knowledge document: %s", path.name)
                    continue
                if (
                    not document["deleted"]
                    and (scope is None or document["scope"] == scope)
                    and (card_code is None or document["card_code"] == card_code)
                ):
                    documents.append(document)
            return documents

    def get(self, file_id: str) -> dict[str, Any] | None:
        validate_id(file_id)
        with self._lock:
            return self._get(file_id)

    def delete(self, file_id: str) -> None:
        validate_id(file_id)
        with self._lock:
            current = self._get(file_id)
            if current is None:
                return
            versions = self._history(file_id)
            current.update(
                deleted=True,
                public=False,
                approved=False,
                revision=max(current["revision"], versions[0]["revision"] if versions else 0) + 1,
            )
            self._save(current)

    def history(self, file_id: str) -> list[dict[str, Any]]:
        validate_id(file_id)
        with self._lock:
            return self._history(file_id)

    def rollback(self, file_id: str, revision: int) -> dict[str, Any]:
        validate_id(file_id)
        if type(revision) is not int or revision < 1:
            raise ValueError("Invalid revision")
        with self._lock:
            versions = self._history(file_id)
            target = next((item for item in versions if item["revision"] == revision), None)
            if target is None:
                raise KeyError("Knowledge revision not found")
            current = self._get(file_id)
            target.update(
                revision=versions[0]["revision"] + 1,
                deleted=False,
                public=current["public"] if current else False,
                approved=current["approved"] if current else False,
            )
            return self._save(target)

    def search(
        self, query: str, card_code: str | None = None, limit: int = 4
    ) -> list[dict[str, Any]]:
        if card_code is not None:
            validate_id(card_code)
        if not isinstance(query, str) or type(limit) is not int:
            raise ValueError("Invalid search arguments")
        if limit <= 0 or not query.strip():
            return []
        terms = set(re.findall(r"[a-z0-9_]+|[\u3400-\u9fff]{1,2}", query[:2000].lower()))
        if not terms:
            return []
        with self._lock:
            candidates = []
            for document in self.list_files():
                if document["public"] is not True or document["approved"] is not True:
                    continue
                if document["scope"] != "company" and document["card_code"] != card_code:
                    continue
                body, title = document["content"].lower(), document["title"].lower()
                score = sum(3 * (term in title) + (term in body) for term in terms)
                if score:
                    candidates.append((score, document))
            candidates.sort(key=lambda item: (-item[0], item[1]["file_id"]))
            result, remaining = [], 6000
            for _, document in candidates[: min(limit, 4)]:
                original = document["content"]
                document["content"] = bounded_text(original, min(1500, remaining))
                remaining -= estimate_tokens(document["content"])
                document["truncated"] = document["content"] != original
                result.append(document)
            return result
