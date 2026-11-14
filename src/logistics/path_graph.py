"""Site graph from the grid: nodes are walkable cells, edges join 4-neighbours (owner: M3)."""
from __future__ import annotations


class PathGraph:
    def __init__(self, grid):
        self.grid = grid
        self.adj = {c: grid.neighbors4(c) for c in grid.cells()}

    def neighbors(self, cell) -> list:
        return self.adj.get(cell, [])

    def __contains__(self, cell) -> bool:
        return cell in self.adj
