"""Pheromone markers: deposit, read, evaporate (owner: M2).

Robots that place a block mark the surrounding walkable cells. The marks fade over time, so they
only point at *recent* construction activity. Robots read the marks inside their sensing radius.
"""
from __future__ import annotations

import numpy as np


class PheromoneField:
    def __init__(self, width: int, height: int, evaporation: float = 0.05, cap: float = 1.0):
        self.grid = np.zeros((height, width))
        self.evaporation, self.cap = evaporation, cap
        self.width, self.height = width, height

    def deposit(self, x: int, y: int, amount: float = 1.0) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y, x] = min(self.cap, self.grid[y, x] + amount)

    def read(self, x: int, y: int) -> float:
        return float(self.grid[y, x]) if 0 <= x < self.width and 0 <= y < self.height else 0.0

    def evaporate(self) -> None:
        self.grid *= (1.0 - self.evaporation)
        self.grid[self.grid < 1e-3] = 0.0

    def as_list(self) -> list:
        return np.round(self.grid, 2).tolist()


_ACTIVE: PheromoneField | None = None


def set_active(f: PheromoneField | None) -> None:
    global _ACTIVE
    _ACTIVE = f


def deposit(x, y, amount=1.0) -> None:
    _ACTIVE.deposit(x, y, amount)


def read(x, y) -> float:
    return _ACTIVE.read(x, y)


def evaporate() -> None:
    _ACTIVE.evaporate()
