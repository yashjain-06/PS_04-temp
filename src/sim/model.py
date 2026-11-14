"""The swarm model: environment + robots + one tick loop (owner: M1; M2/M3/M4 integrate here).

Plain Python (no Mesa dependency), so it runs and is testable anywhere.
There is NO central scheduler: each tick every active robot runs its own FSM in a seeded random
order. The model only enforces physics (one robot per cell, legal placements) and records metrics.
"""
from __future__ import annotations

import dataclasses
from collections import deque

from src.agents import stigmergy
from src.agents.builder import Builder
from src.env import reachability
from src.env import rules as rules_mod
from src.env.blueprint import load_blueprint
from src.env.depot import Depots
from src.env.grid import Grid
from src.env.rules import RuleSet
from src.logistics import router as router_mod
from src.logistics.congestion import CongestionStats
from src.logistics.router import Router
from src.sim import snapshot as snap_mod
from src.sim.events import EventLog
from src.sim.failure import fail_agents
from src.sim.seeding import make_rng
from src.utils.config import load_config

_VERIFIED: set = set()


class SwarmModel:
    def __init__(self, blueprint="blueprints/wall_with_opening.json", n_agents=10, fail_rate=0.0, use_aco=False,
                 seed=42, fail_at_tick=100, max_ticks=3000, cfg=None, depots=None, **_):
        cfg = cfg or load_config()
        bp = load_blueprint(blueprint)
        if depots:                                           # e.g. positions from PSO (src/logistics/pso.py)
            bp = dataclasses.replace(bp, depots=tuple(tuple(d) for d in depots))
        self.blueprint, self.seed = bp, seed
        self.n_agents, self.fail_rate, self.fail_at_tick, self.max_ticks = n_agents, fail_rate, fail_at_tick, max_ticks
        self.grid = Grid(bp.width, bp.height, bp.obstacles, bp.depots)
        self.depots = Depots(bp.depots)
        self.rules = RuleSet(bp, self.grid)
        if blueprint not in _VERIFIED and not depots:                       # one cheap dead-end check per blueprint
            self.rules.check_buildable(trials=3, seed=0)
            _VERIFIED.add(blueprint)
        self.sensing_radius = int(cfg["sensing"]["radius"])
        self.load_time, self.patience = int(cfg["agents"]["load_time"]), int(cfg["agents"]["patience"])
        st = cfg["stigmergy"]
        self.pheromone = stigmergy.PheromoneField(bp.width, bp.height, st["evaporation"])
        self.pheromone_deposit, self.pheromone_threshold = float(st["deposit"]), float(st["threshold"])
        self.router = Router(self.grid, use_aco=bool(use_aco), seed=seed, aco_cfg=cfg["aco"],
                             baseline_kind=cfg["logistics"].get("baseline", "straight"))
        self.congestion = CongestionStats(bp.width, bp.height)
        self.events = EventLog()
        self.rng = make_rng(seed, "order")
        self.occupancy: dict = {}
        self.tick, self.blocks_placed, self.completed_tick = 0, 0, None
        self.agents = [Builder(i, x, y, self, seed) for i, (x, y) in enumerate(self._spawn_cells(n_agents))]
        for a in self.agents:
            self.occupancy[(a.x, a.y)] = a
        rules_mod.set_active(self.rules)
        stigmergy.set_active(self.pheromone)
        router_mod.set_active(self.router)

    # ---- setup ------------------------------------------------------------------------------
    def _spawn_cells(self, n: int) -> list:
        seen, q, out = set(self.depots.positions), deque(self.depots.positions), []
        while q and len(out) < n:
            cur = q.popleft()
            for nb in self.grid.neighbors4(cur):
                if nb not in seen and nb not in self.rules.targets:
                    seen.add(nb)
                    out.append(nb)
                    q.append(nb)
        if len(out) < n:
            raise ValueError(f"not enough free cells near the depots for {n} robots")
        return out[:n]

    # ---- physics the model enforces ---------------------------------------------------------
    def cell_status(self, cell) -> str:
        if not self.grid.passable(*cell) or cell in self.rules.structure:
            return "block"
        occ = self.occupancy.get(cell)
        if occ is None:
            return "free"
        return "block" if occ.failed else "robot"

    def move_agent(self, a, cell) -> None:
        del self.occupancy[(a.x, a.y)]
        a.last = (a.x, a.y)
        a.x, a.y = cell
        self.occupancy[cell] = a

    def try_place(self, a, cell) -> bool:
        if cell in self.occupancy or not self.rules.can_place(*cell):
            return False
        self.rules.place(*cell)
        self.blocks_placed += 1
        self.events.record(self.tick, "placed", agent=a.id, x=cell[0], y=cell[1])
        for c in [(a.x, a.y)] + [n for n in self.grid.neighbors4((a.x, a.y)) if n not in self.rules.structure]:
            self.pheromone.deposit(c[0], c[1], self.pheromone_deposit)
        return True

    def _blocks_site(self, a) -> bool:
        """Would this dead robot make the build impossible (sit on a build cell/depot, or seal off targets)?"""
        pos = (a.x, a.y)
        if pos in self.rules.targets or self.depots.is_depot(pos):
            return True
        dead = {(b.x, b.y) for b in self.agents if b.failed}
        built = self.rules.structure.cells
        return not reachability.all_reachable(self.grid, self.depots.positions, built | dead, self.rules.targets - built)

    def _relocate_failed(self) -> None:
        """Fault model (documented in docs/limitations.md): a robot that dies stops acting and stays as an
        obstacle, but if that spot would make the site physically unbuildable it first coasts to the nearest
        harmless cell. Without this, two dead robots in a gap could seal the site and no swarm could finish."""
        for a in self.agents:
            if not a.failed or a.relocated:
                continue
            a.relocated = True
            if not self._blocks_site(a):
                continue
            seen, q, order = {(a.x, a.y)}, deque([(a.x, a.y)]), []
            while q:
                cur = q.popleft()
                for nb in self.grid.neighbors4(cur):
                    if nb not in seen:
                        seen.add(nb)
                        order.append(nb)
                        q.append(nb)
            for cand in order:
                if cand in self.occupancy or cand in self.rules.structure or cand in self.rules.targets \
                        or self.depots.is_depot(cand):
                    continue
                self.move_agent(a, cand)
                if not self._blocks_site(a):
                    break

    # ---- the tick ----------------------------------------------------------------------------
    def step(self) -> None:
        if self.build_complete():
            return
        self.tick += 1
        if self.fail_rate > 0 and self.tick == self.fail_at_tick:
            fail_agents(self, self.fail_rate, self.tick, self.seed)
        self._relocate_failed()
        self.pheromone.evaporate()
        for i in self.rng.permutation(len(self.agents)):
            a = self.agents[int(i)]
            if a.failed:
                continue
            a.active_ticks += 1
            a.step()
        self.congestion.record_positions((a.x, a.y) for a in self.agents if not a.failed)
        if self.build_complete():
            self.completed_tick = self.tick
            self.events.record(self.tick, "complete")

    # ---- contract used by the web app, runner and interface checker -------------------------
    def build_complete(self) -> bool:
        return len(self.rules.structure) == len(self.rules.targets)

    def accuracy(self) -> float:
        return len(self.rules.structure.cells & self.rules.targets) / len(self.rules.targets)

    def agent_ticks(self) -> int:
        return sum(a.active_ticks for a in self.agents)

    def structure_cells(self) -> list:
        return [(x, y, 0) for x, y in sorted(self.rules.structure.cells)]

    def blueprint_cells(self) -> list:
        return [tuple(c) for c in self.blueprint.cells]

    @property
    def blocked_ticks(self) -> int:
        return self.congestion.blocked_ticks

    def snapshot(self) -> dict:
        return snap_mod.snapshot(self)


def build_model(**params) -> SwarmModel:
    return SwarmModel(**params)
