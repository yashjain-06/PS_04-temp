"""Event log for placements, failures and completion (owner: M4).

Models record events with `model.events.record(tick, kind, **data)`.
Kinds used so far: "placed", "failed", "complete".
"""
from __future__ import annotations

import csv
from pathlib import Path


class EventLog:
    def __init__(self):
        self.rows: list[dict] = []

    def record(self, tick: int, kind: str, **data) -> None:
        self.rows.append({"tick": tick, "kind": kind, **data})

    def of_kind(self, kind: str) -> list[dict]:
        return [r for r in self.rows if r["kind"] == kind]

    def count(self, kind: str) -> int:
        return len(self.of_kind(kind))

    def to_csv(self, path: str | Path) -> None:
        keys = sorted({k for r in self.rows for k in r}, key=lambda k: (k not in ("tick", "kind"), k))
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(self.rows)
