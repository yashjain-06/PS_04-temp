"""get_route(src, dst): one interface, swappable baseline / ACO (owner: M3)."""
from __future__ import annotations

from src.logistics import baseline
from src.logistics.aco import AntColony
from src.logistics.path_graph import PathGraph
from src.sim.seeding import make_rng


class Router:
    def __init__(self, grid, use_aco=False, seed=0, aco_cfg=None, baseline_kind="straight"):
        self.grid, self.use_aco, self.baseline_kind = grid, use_aco, baseline_kind
        self.graph = PathGraph(grid)
        self.rng = make_rng(seed, "router")
        self.aco = AntColony(self.graph, seed=seed, **(aco_cfg or {})) if use_aco else None

    def get_route(self, src, dst, blocked=()) -> list:
        """Cells to walk from src to dst (excludes src, includes dst). Never raises.

        `blocked` (optional) = cells the caller already knows are built. ACO plans around them;
        the naive baseline ignores them on purpose."""
        src, dst = tuple(src), tuple(dst)
        if src == dst:
            return []
        if self.use_aco:
            return self.aco.route(src, dst, blocked)
        if self.baseline_kind == "random":
            return baseline.random_route(src, dst, self.rng, self.grid)
        return baseline.straight_route(src, dst)


_ACTIVE: Router | None = None


def set_active(r: Router | None) -> None:
    global _ACTIVE
    _ACTIVE = r


def get_route(src, dst, blocked=()) -> list:
    if _ACTIVE is None:
        raise RuntimeError("no active Router; build a model first")
    return _ACTIVE.get_route(src, dst, blocked)
