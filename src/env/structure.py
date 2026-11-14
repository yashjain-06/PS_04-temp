"""Structure layer: which cells have a block (owner: M1). Blocks are never removed."""
from __future__ import annotations


class Structure:
    def __init__(self):
        self.cells: set = set()
        self.version = 0

    def add(self, cell) -> None:
        self.cells.add(tuple(cell))
        self.version += 1

    def __contains__(self, cell) -> bool:
        return tuple(cell) in self.cells

    def __len__(self) -> int:
        return len(self.cells)

    def as_list(self) -> list:
        return [[x, y, 0] for x, y in sorted(self.cells, key=lambda c: (c[1], c[0]))]
