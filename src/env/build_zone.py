"""Build zone: the set of target cells (owner: M1)."""
from __future__ import annotations


class BuildZone:
    def __init__(self, targets):
        self.targets = frozenset(tuple(t) for t in targets)

    def __contains__(self, cell) -> bool:
        return tuple(cell) in self.targets

    def remaining(self, built) -> set:
        return set(self.targets) - set(built)

    def progress(self, built) -> float:
        return len(self.targets & set(built)) / len(self.targets)
