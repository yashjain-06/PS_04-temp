"""Metric definitions, frozen at hour 2 (owner: M4).

build_time : ticks until the structure is complete (max_ticks if never completed)
accuracy   : |structure ∩ blueprint| / |blueprint|            (1.0 = every target cell built)
exact      : structure == blueprint (no missing AND no extra cells)
efficiency : blocks_placed / agent_ticks  (agent_ticks = sum over agents of ticks they were active)
slowdown   : build_time_with_failures / build_time_without_failures
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

Cell = tuple  # (x, y) or (x, y, z)


def build_time(completed_tick: int | None, max_ticks: int) -> int:
    return max_ticks if completed_tick is None else completed_tick


def accuracy(structure: Iterable[Cell], blueprint: Iterable[Cell]) -> float:
    bp = {tuple(c) for c in blueprint}
    if not bp:
        return 1.0
    st = {tuple(c) for c in structure}
    return len(st & bp) / len(bp)


def is_exact(structure: Iterable[Cell], blueprint: Iterable[Cell]) -> bool:
    return {tuple(c) for c in structure} == {tuple(c) for c in blueprint}


def extra_cells(structure: Iterable[Cell], blueprint: Iterable[Cell]) -> int:
    return len({tuple(c) for c in structure} - {tuple(c) for c in blueprint})


def efficiency(blocks_placed: int, agent_ticks: int) -> float:
    return 0.0 if agent_ticks <= 0 else blocks_placed / agent_ticks


def slowdown(time_with_failures: float, time_without_failures: float) -> float:
    if time_without_failures <= 0:
        raise ValueError("time_without_failures must be > 0")
    return time_with_failures / time_without_failures


@dataclass
class RunMetrics:
    """One row of results/raw/*.csv."""
    seed: int
    blueprint: str
    n_agents: int
    fail_rate: float
    use_aco: bool
    build_time: int
    accuracy: float
    exact: bool
    extra_cells: int
    blocks_placed: int
    agent_ticks: int
    efficiency: float
    completed: bool
    blocked_ticks: int = 0

    def to_row(self) -> dict:
        return asdict(self)
