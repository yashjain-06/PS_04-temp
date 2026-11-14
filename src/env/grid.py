"""Grid: bounds, static obstacles, walkable neighbours (owner: M1)."""
from __future__ import annotations


class Grid:
    def __init__(self, width: int, height: int, obstacles=(), depots=()):
        self.width, self.height = width, height
        self.obstacles = frozenset(tuple(o) for o in obstacles)
        self.depots = tuple(tuple(d) for d in depots)

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_obstacle(self, x: int, y: int) -> bool:
        return (x, y) in self.obstacles

    def passable(self, x: int, y: int) -> bool:
        return self.in_bounds(x, y) and (x, y) not in self.obstacles

    def neighbors4(self, cell) -> list:
        x, y = cell
        return [(nx, ny) for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if self.passable(nx, ny)]

    def cells(self):
        return [(x, y) for y in range(self.height) for x in range(self.width) if (x, y) not in self.obstacles]
