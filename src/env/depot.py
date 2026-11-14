"""Depots: where robots pick up blocks (owner: M1). Supply is unlimited; capacity is one robot per depot cell."""
from __future__ import annotations


class Depots:
    def __init__(self, positions):
        self.positions = tuple(tuple(p) for p in positions)
        self._set = frozenset(self.positions)

    def is_depot(self, cell) -> bool:
        return tuple(cell) in self._set

    def nearest(self, cell, rng=None):
        d = lambda p: abs(p[0] - cell[0]) + abs(p[1] - cell[1])         # noqa: E731
        best = min(d(p) for p in self.positions)
        ties = [p for p in self.positions if d(p) == best]
        return ties[int(rng.integers(len(ties)))] if rng is not None and len(ties) > 1 else ties[0]
