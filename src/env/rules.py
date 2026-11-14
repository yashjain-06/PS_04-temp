"""Placement rules: can_place, is_supported, order_ok, is_occupied (owner: M1).

Frozen interface (docs/interfaces.md): module-level functions act on the *active* RuleSet,
which the model sets with set_active(). Robots call these only for cells they can sense.
"""
from __future__ import annotations

from src.env import reachability
from src.env.depot import Depots
from src.env.grid import Grid
from src.env.rules_compiler import UnbuildableError, compile_rules, verify_buildable
from src.env.structure import Structure


class RuleViolation(RuntimeError):
    pass


class RuleSet:
    def __init__(self, blueprint, grid: Grid | None = None):
        self.blueprint = blueprint
        self.grid = grid or Grid(blueprint.width, blueprint.height, blueprint.obstacles, blueprint.depots)
        self.depots = Depots(blueprint.depots)
        compiled = compile_rules(blueprint)
        self.targets, self.seeds = compiled.targets, compiled.seeds
        self.structure = Structure()
        self._order_cache: dict = {}

    def clone(self) -> "RuleSet":
        return RuleSet(self.blueprint, self.grid)

    def is_occupied(self, x, y, z=0) -> bool:
        return (x, y) in self.structure or self.grid.is_obstacle(x, y)

    def is_supported(self, x, y, z=0) -> bool:
        if (x, y) in self.seeds:
            return True
        return any(n in self.structure for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    def order_ok(self, x, y, z=0) -> bool:
        c = (x, y)
        if c not in self.targets or c in self.structure:
            return False
        ok = self._order_cache.get(c)
        if ok is None:
            blocked = self.structure.cells | {c}
            ok = reachability.all_reachable(self.grid, self.depots.positions, blocked, self.targets - blocked)
            self._order_cache[c] = ok
        return ok

    def can_place(self, x, y, z=0) -> bool:
        c = (x, y)
        return (c in self.targets and c not in self.structure
                and self.is_supported(x, y) and self.order_ok(x, y))

    def place(self, x, y, z=0) -> None:
        if not self.can_place(x, y):
            raise RuleViolation(f"illegal placement at ({x},{y})")
        self.structure.add((x, y))
        self._order_cache.clear()

    def check_buildable(self, trials: int = 1, seed: int = 0) -> None:
        ok, stuck = verify_buildable(self.clone, trials, seed)
        if not ok:
            raise UnbuildableError(f"blueprint {self.blueprint.name!r} can reach a dead end; stuck with {stuck}")


_ACTIVE: RuleSet | None = None


def set_active(rs: RuleSet | None) -> None:
    global _ACTIVE
    _ACTIVE = rs


def _rs() -> RuleSet:
    if _ACTIVE is None:
        raise RuntimeError("no active RuleSet; build a model first")
    return _ACTIVE


def can_place(x, y, z=0) -> bool:
    return _rs().can_place(x, y, z)


def is_supported(x, y, z=0) -> bool:
    return _rs().is_supported(x, y, z)


def order_ok(x, y, z=0) -> bool:
    return _rs().order_ok(x, y, z)


def is_occupied(x, y, z=0) -> bool:
    return _rs().is_occupied(x, y, z)
