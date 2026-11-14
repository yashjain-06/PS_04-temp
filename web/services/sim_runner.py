"""Holds the current simulation and steps it (owner: M4).

Model creation goes through src/sim/factory.py (fake until the first integration).
"""
from __future__ import annotations

import threading

from src.experiments import metrics as M
from src.sim.factory import make_model


class SimRunner:
    def __init__(self):
        self.lock = threading.RLock()
        self.model = None
        self.params: dict = {}
        self.running = False
        self.baseline_time = None      # filled by experiment runs later, for slowdown

    def start(self, params: dict) -> dict:
        with self.lock:
            self.params = params
            self.model = make_model(params)
            self.running = True
            return self.model.snapshot()

    def step(self, n: int = 1) -> dict | None:
        with self.lock:
            if self.model is None:
                return None
            for _ in range(max(1, n)):
                self.model.step()
            if self.model.build_complete():
                self.running = False
            return self.model.snapshot()

    def state(self) -> dict | None:
        with self.lock:
            return self.model.snapshot() if self.model else None

    def pause(self) -> None:
        with self.lock:
            self.running = False

    def resume(self) -> None:
        with self.lock:
            if self.model and not self.model.build_complete():
                self.running = True

    def reset(self) -> None:
        with self.lock:
            self.model, self.running = None, False

    def metrics(self) -> dict:
        with self.lock:
            m = self.model
            if m is None:
                return {}
            done = m.build_complete()
            bt = M.build_time(m.tick if done else None, m.max_ticks)
            return {
                "tick": m.tick, "complete": done, "build_time": bt if done else None,
                "accuracy": round(m.accuracy(), 3),
                "efficiency": round(M.efficiency(m.blocks_placed, m.agent_ticks()), 4),
                "slowdown": (round(M.slowdown(bt, self.baseline_time), 2)
                             if done and self.baseline_time else None),
            }

