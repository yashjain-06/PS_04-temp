"""YAML config loading with defaults + overrides (owner: M4)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "configs" / "default.yaml"


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config(path: str | Path | None = None, overrides: dict | None = None) -> dict[str, Any]:
    """Load default.yaml, merge `path` on top (if given), then `overrides`."""
    cfg = load_yaml(DEFAULT_PATH)
    for section in ("aco", "stigmergy"):                  # per-topic files live beside default.yaml
        f = DEFAULT_PATH.parent / f"{section}.yaml"
        if f.exists():
            cfg[section] = _deep_merge(load_yaml(f), cfg.get(section, {}))
    if path is not None and Path(path).resolve() != DEFAULT_PATH:
        cfg = _deep_merge(cfg, load_yaml(path))
    if overrides:
        cfg = _deep_merge(cfg, overrides)
    return cfg
