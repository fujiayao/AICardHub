"""Load the application's fixed built-in skill, never a user-selected path."""

from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def load_skill() -> str:
    return Path(__file__).with_name("SKILL.md").read_text(encoding="utf-8")
