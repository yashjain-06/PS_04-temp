"""Compile a blueprint into local placement rules and check they are buildable (owner: M1).

Compiled facts (static, every robot may carry them):
  targets : cells to build          seeds : cells placeable on bare ground (one per connected piece,
                                    the piece's cell nearest a depot)
Rules (evaluated in rules.RuleSet):  a cell is placeable iff it is a target, not built,
  supported (a seed, or 4-adjacent to a built block) and order_ok (placing it keeps every other
  unbuilt target reachable from a depot).
"""
from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass


class UnbuildableError(RuntimeError):
    pass


@dataclass(frozen=True)
class CompiledRules:
    targets: frozenset
    seeds: frozenset


def _components(targets: frozenset) -> list:
    left, comps = set(targets), []
    while left:
        start = min(left, key=lambda c: (c[1], c[0]))
        comp, q = {start}, deque([start])
        left.discard(start)
        while q:
            x, y = q.popleft()
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if n in left:
                    left.discard(n)
                    comp.add(n)
                    q.append(n)
        comps.append(comp)
    return comps


def compile_rules(blueprint) -> CompiledRules:
    targets = blueprint.targets
    seeds = set()
    for comp in _components(targets):
        dist = lambda c: min(abs(c[0] - d[0]) + abs(c[1] - d[1]) for d in blueprint.depots)   # noqa: E731
        seeds.add(min(comp, key=lambda c: (dist(c), c[1], c[0])))
    return CompiledRules(targets, frozenset(seeds))


def verify_buildable(make_ruleset, trials: int = 20, seed: int = 0) -> tuple:
    """Build the blueprint in `trials` random legal orders. Returns (ok, stuck_state_or_None).

    An empirical check, not a proof: if every random order finishes, no dead end was found.
    """
    rnd = random.Random(seed)
    for _ in range(trials):
        rs = make_ruleset()
        while len(rs.structure) < len(rs.targets):
            options = [c for c in sorted(rs.targets - rs.structure.cells) if rs.can_place(*c)]
            if not options:
                return False, sorted(rs.structure.cells)
            rs.place(*rnd.choice(options))
    return True, None
