"""Safe blueprint path handling shared by the API routes (owner: M4)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BP_DIR = (ROOT / "blueprints").resolve()
NAME_OK = re.compile(r"^[A-Za-z0-9_\-]{1,40}$")


def safe_blueprint(name: str) -> str:
    """Return a repo-relative path for a blueprint under blueprints/, or raise ValueError (blocks path traversal)."""
    p = (ROOT / str(name)).resolve()
    if BP_DIR not in p.parents or p.suffix not in (".json", ".txt") or not p.exists():
        raise ValueError(f"unknown blueprint: {name}")
    return p.relative_to(ROOT).as_posix()


def list_blueprints() -> list:
    out = [p.relative_to(ROOT).as_posix() for p in BP_DIR.rglob("*") if p.suffix in (".json", ".txt")]
    return sorted(out)
