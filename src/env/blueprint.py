"""Load and validate blueprints from JSON or ASCII text (owner: M1).

JSON : {name, width, height, depth, depots: [[x,y]], obstacles: [[x,y]], cells: [[x,y,z]]}
ASCII: one char per cell: '#' target block, '.' free, 'D' depot, 'X' obstacle   (extension .txt)
Only flat (depth 1, z = 0) blueprints are supported; 3D is out of scope and rejected explicitly.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class BlueprintError(ValueError):
    pass


@dataclass(frozen=True)
class Blueprint:
    name: str
    width: int
    height: int
    depth: int
    depots: tuple
    obstacles: tuple
    cells: tuple            # ((x, y, z), ...)

    @property
    def targets(self) -> frozenset:
        return frozenset((x, y) for x, y, _ in self.cells)

    def to_json(self) -> dict:
        return {"name": self.name, "width": self.width, "height": self.height, "depth": self.depth,
                "depots": [list(d) for d in self.depots], "obstacles": [list(o) for o in self.obstacles],
                "cells": [list(c) for c in self.cells]}


def parse_blueprint(d: dict, name: str = "blueprint") -> Blueprint:
    try:
        w, h = int(d["width"]), int(d["height"])
        depots = tuple(tuple(map(int, p[:2])) for p in d["depots"])
        obstacles = tuple(tuple(map(int, p[:2])) for p in d.get("obstacles", []))
        cells = tuple((int(c[0]), int(c[1]), int(c[2]) if len(c) > 2 else 0) for c in d["cells"])
    except (KeyError, TypeError, ValueError) as e:
        raise BlueprintError(f"malformed blueprint: {e!r}") from e
    if int(d.get("depth", 1)) != 1 or any(z != 0 for _, _, z in cells):
        raise BlueprintError("only flat (depth 1, z=0) blueprints are supported")
    if not cells:
        raise BlueprintError("blueprint has no target cells")
    if not depots:
        raise BlueprintError("blueprint needs at least one depot")
    inb = lambda x, y: 0 <= x < w and 0 <= y < h                       # noqa: E731
    obst = set(obstacles)
    for x, y, _ in cells:
        if not inb(x, y):
            raise BlueprintError(f"target ({x},{y}) is outside the grid")
        if (x, y) in obst:
            raise BlueprintError(f"target ({x},{y}) is on an obstacle")
    if len({(x, y) for x, y, _ in cells}) != len(cells):
        raise BlueprintError("duplicate target cells")
    for p in depots:
        if not inb(*p) or p in obst or p in {(x, y) for x, y, _ in cells}:
            raise BlueprintError(f"invalid depot {p}")
    return Blueprint(d.get("name", name), w, h, 1, depots, obstacles, cells)


def parse_ascii(text: str, name: str = "blueprint") -> Blueprint:
    rows = [r.rstrip("\n") for r in text.splitlines() if r.strip()]
    h, w = len(rows), max(len(r) for r in rows)
    cells, depots, obst = [], [], []
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "#":
                cells.append([x, y, 0])
            elif ch == "D":
                depots.append([x, y])
            elif ch == "X":
                obst.append([x, y])
            elif ch not in ". ":
                raise BlueprintError(f"unknown character {ch!r} at ({x},{y})")
    return parse_blueprint({"width": w, "height": h, "depots": depots, "obstacles": obst, "cells": cells}, name)


def load_blueprint(path) -> Blueprint:
    p = Path(path)
    if not p.exists():
        p = ROOT / path
    if not p.exists():
        raise BlueprintError(f"blueprint not found: {path}")
    if p.suffix == ".txt":
        return parse_ascii(p.read_text(), p.stem)
    return parse_blueprint(json.loads(p.read_text()), p.stem)
