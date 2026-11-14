"""Traffic and congestion statistics (owner: M3)."""
from __future__ import annotations

import numpy as np


class CongestionStats:
    def __init__(self, width: int, height: int):
        self.visits = np.zeros((height, width), dtype=np.int64)
        self.blocked_ticks = 0           # robot-ticks spent unable to move because another robot was in the way
        self.depot_queue_ticks = 0       # robot-ticks spent waiting within 2 cells of a depot

    def record_positions(self, positions) -> None:
        for x, y in positions:
            self.visits[y, x] += 1

    def heat(self) -> list:
        m = self.visits.max()
        return (np.round(self.visits / m, 2) if m else self.visits.astype(float)).tolist()
