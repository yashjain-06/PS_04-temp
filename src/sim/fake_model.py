"""FakeModel: stands in for M1's real model until the first integration (owner: M4).

It produces snapshots in the frozen shape (docs/interfaces.md). It is NOT decentralised:
it hands out targets from a list. That is fine for UI work, and must never ship as the demo.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.sim.events import EventLog
from src.sim.failure import fail_agents
from src.sim.seeding import make_rng

ROOT = Path(__file__).resolve().parents[2]


class FakeModel:
    def __init__(self, blueprint: str = "blueprints/wall_with_opening.json", n_agents: int = 10,
                 fail_rate: float = 0.0, use_aco: bool = False, seed: int = 42,
                 fail_at_tick: int = 60, max_ticks: int = 3000, **_):
        bp = json.loads((ROOT / blueprint).read_text())
        self.width, self.height, self.depth = bp["width"], bp["height"], bp.get("depth", 1)
        self.blueprint = [tuple(c) for c in bp["cells"]]
        self.depots = [tuple(d) for d in bp["depots"]]
        self.rng = make_rng(seed, "fake")
        self.seed = seed
        self.events = EventLog()
        self.use_aco = use_aco
        self.max_ticks = max_ticks
        self.fail_rate, self.fail_at_tick = fail_rate, fail_at_tick
        self.tick = 0
        self.completed_tick = None
        self.structure: list[tuple] = []
        self.pending = sorted(self.blueprint, key=lambda c: (c[0], c[1]))   # build left to right
        self.claimed: dict[int, tuple] = {}
        self.pher = [[0.0] * self.width for _ in range(self.height)]
        self.agents = []
        for i in range(n_agents):
            dx, dy = self.depots[i % len(self.depots)]
            self.agents.append({"id": i, "x": dx, "y": dy, "state": "seek",
                                "carrying": False, "failed": False, "active_ticks": 0})
        self.blocks_placed = 0

    # -- helpers -----------------------------------------------------------------
    def _depot_for(self, a):
        return min(self.depots, key=lambda d: abs(d[0] - a["x"]) + abs(d[1] - a["y"]))

    def _move_toward(self, a, tx, ty):
        dx, dy = tx - a["x"], ty - a["y"]
        if dx == 0 and dy == 0:
            return True
        if abs(dx) >= abs(dy) and dx != 0:
            a["x"] += 1 if dx > 0 else -1
        elif dy != 0:
            a["y"] += 1 if dy > 0 else -1
        return False

    # -- simulation ----------------------------------------------------------------
    def step(self):
        if self.completed_tick is not None:
            return
        self.tick += 1
        if self.fail_rate > 0 and self.tick == self.fail_at_tick:
            for i in fail_agents(self, self.fail_rate, self.tick, self.seed):
                self.claimed.pop(i, None)           # its claimed cell becomes free again
        for row in self.pher:                                    # evaporation
            for x in range(self.width):
                row[x] *= 0.97
        order = self.rng.permutation(len(self.agents))
        for idx in order:
            a = self.agents[int(idx)]
            if a["failed"]:
                continue
            a["active_ticks"] += 1
            if a["state"] == "seek":
                dx, dy = self._depot_for(a)
                if self._move_toward(a, dx, dy):
                    a["carrying"], a["state"] = True, "carry"
            elif a["state"] == "carry":
                if a["id"] not in self.claimed:
                    free = [c for c in self.pending if c not in self.claimed.values()]
                    if not free:
                        continue
                    self.claimed[a["id"]] = free[0]
                tx, ty, _ = self.claimed[a["id"]]
                self.pher[a["y"]][a["x"]] = min(1.0, self.pher[a["y"]][a["x"]] + 0.2)
                if self._move_toward(a, tx, ty):
                    a["state"] = "place"
            elif a["state"] == "place":
                cell = self.claimed.pop(a["id"])
                self.pending.remove(cell)
                self.structure.append(cell)
                self.blocks_placed += 1
                self.events.record(self.tick, "placed", agent=a["id"], x=cell[0], y=cell[1])
                a["carrying"], a["state"] = False, "return"
            elif a["state"] == "return":
                dx, dy = self._depot_for(a)
                if self._move_toward(a, dx, dy):
                    a["state"] = "seek"
        if not self.pending:
            self.completed_tick = self.tick
            self.events.record(self.tick, "complete")
        elif self.tick >= self.max_ticks:
            self.completed_tick = None

    def structure_cells(self) -> list[tuple]:
        return list(self.structure)

    def blueprint_cells(self) -> list[tuple]:
        return list(self.blueprint)

    def build_complete(self) -> bool:
        return not self.pending

    def accuracy(self) -> float:
        return len(self.structure) / len(self.blueprint) if self.blueprint else 1.0

    def snapshot(self) -> dict:
        failed = sum(a["failed"] for a in self.agents)
        return {
            "tick": self.tick,
            "grid": {"width": self.width, "height": self.height, "depth": self.depth},
            "blueprint": [list(c) for c in self.blueprint],
            "structure": [list(c) for c in self.structure],
            "depots": [list(d) for d in self.depots],
            "obstacles": [], "traffic": [[0.0] * self.width for _ in range(self.height)],
            "agents": [{k: a[k] for k in ("id", "x", "y", "state", "carrying", "failed")} for a in self.agents],
            "pheromone": [[round(v, 2) for v in row] for row in self.pher],
            "metrics": {"accuracy": round(self.accuracy(), 3), "placed": self.blocks_placed,
                        "active_agents": len(self.agents) - failed, "failed_agents": failed,
                        "complete": self.build_complete()},
        }

    def agent_ticks(self) -> int:
        return sum(a["active_ticks"] for a in self.agents)
