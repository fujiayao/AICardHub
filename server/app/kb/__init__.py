"""File-backed knowledge engine; callers offload store operations to a thread."""

from app.kb.store import KnowledgeStore

__all__ = ["KnowledgeStore"]
