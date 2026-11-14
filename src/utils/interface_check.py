"""Verify that the real code matches docs/interfaces.md (owner: M4).

Used by scripts/check_interfaces.py and tests/test_interfaces.py.
Each check returns (name, ok, detail).
"""
from __future__ import annotations

import importlib
import json

MODULE_API = {
    "src.env.rules": ["can_place", "is_supported", "order_ok", "is_occupied"],
    "src.env.verify": ["accuracy"],
    "src.agents.sensing": ["observe"],
    "src.agents.stigmergy": ["deposit", "read", "evaporate"],
    "src.logistics.router": ["get_route"],
    "src.sim.failure": ["fail_agents"],
}
MODEL_METHODS = ["step", "snapshot", "build_complete", "accuracy", "agent_ticks",
                 "structure_cells", "blueprint_cells"]
MODEL_ATTRS = ["tick", "max_ticks", "blocks_placed", "agents", "events"]
SNAPSHOT_KEYS = ["tick", "grid", "blueprint", "structure", "depots", "obstacles", "agents", "pheromone", "traffic", "metrics"]
AGENT_KEYS = {"id", "x", "y", "state", "carrying", "failed"}
AGENT_STATES = {"seek", "carry", "place", "return"}
METRIC_KEYS = ["accuracy", "placed", "active_agents", "failed_agents"]


def check_modules() -> list[tuple]:
    out = []
    for mod, names in MODULE_API.items():
        try:
            m = importlib.import_module(mod)
        except Exception as e:                                   # noqa: BLE001
            out.append((mod, False, f"import failed: {e!r}"))
            continue
        for n in names:
            ok = callable(getattr(m, n, None))
            out.append((f"{mod}.{n}", ok, "ok" if ok else "MISSING"))
    return out


def check_model(model, max_ticks: int = 3000) -> list[tuple]:
    out = []
    for n in MODEL_METHODS:
        out.append((f"model.{n}()", callable(getattr(model, n, None)), ""))
    for n in MODEL_ATTRS:
        out.append((f"model.{n}", hasattr(model, n), ""))
    if any(not ok for _, ok, _ in out):
        return out                                               # no point running further
    for _ in range(3):
        model.step()
    snap = model.snapshot()
    out.append(("snapshot keys", all(k in snap for k in SNAPSHOT_KEYS),
                f"missing: {[k for k in SNAPSHOT_KEYS if k not in snap]}"))
    try:
        json.dumps(snap)
        out.append(("snapshot JSON-safe", True, ""))
    except TypeError as e:
        out.append(("snapshot JSON-safe", False, str(e)))
    agents = snap.get("agents", [])
    out.append(("agent keys", bool(agents) and all(set(a) == AGENT_KEYS for a in agents),
                f"expected {sorted(AGENT_KEYS)}"))
    out.append(("agent states valid", all(a.get("state") in AGENT_STATES for a in agents),
                f"allowed {sorted(AGENT_STATES)}"))
    out.append(("metrics keys", all(k in snap.get("metrics", {}) for k in METRIC_KEYS), ""))
    g = snap.get("grid", {})
    out.append(("agents inside grid", all(0 <= a["x"] < g.get("width", 0) and 0 <= a["y"] < g.get("height", 0)
                                           for a in agents), ""))
    solid = {tuple(o) for o in snap.get("obstacles", [])} | {tuple(c[:2]) for c in snap.get("structure", [])}
    out.append(("no robot inside a block or rock", not any((a["x"], a["y"]) in solid for a in agents), ""))
    cells = [tuple(c) for c in model.structure_cells()]
    out.append(("no two blocks in one cell", len(cells) == len(set(cells)), ""))
    pos = [(a["x"], a["y"]) for a in agents if not a["failed"]]
    out.append(("one robot per cell", len(pos) == len(set(pos)), "FakeModel has no collision handling" if pos else ""))
    while not model.build_complete() and model.tick < max_ticks:
        model.step()
    done = model.build_complete()
    out.append(("build completes", done, f"tick {model.tick}"))
    bp, st = {tuple(c) for c in model.blueprint_cells()}, {tuple(c) for c in model.structure_cells()}
    out.append(("structure == blueprint (exact)", done and bp == st, f"missing {len(bp - st)}, extra {len(st - bp)}"))
    return out
