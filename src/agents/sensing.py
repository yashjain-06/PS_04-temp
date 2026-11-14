"""Limited-radius sensing (owner: M2). This is the ONLY way a robot learns about the world.

A robot receives: built cells, other robots, obstacles, pheromone and unbuilt target cells,
all restricted to the Chebyshev window of the given radius around itself. It also carries the
static blueprint and site map (documented in docs/decentralisation.md).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Observation:
    center: tuple
    radius: int
    built: set = field(default_factory=set)
    targets_unbuilt: set = field(default_factory=set)
    robots: dict = field(default_factory=dict)       # (x, y) -> robot id, excluding the observer
    obstacles: set = field(default_factory=set)
    pheromone: dict = field(default_factory=dict)    # (x, y) -> level, only cells with a mark

    def cells_seen(self) -> set:
        return self.built | self.targets_unbuilt | set(self.robots) | self.obstacles | set(self.pheromone)


def observe(agent, radius: int) -> Observation:
    m, cx, cy = agent.model, agent.x, agent.y
    obs = Observation((cx, cy), radius)
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            if not m.grid.in_bounds(x, y):
                continue
            c = (x, y)
            if c in m.grid.obstacles:
                obs.obstacles.add(c)
            if c in m.rules.structure:
                obs.built.add(c)
            elif c in m.rules.targets:
                obs.targets_unbuilt.add(c)
            other = m.occupancy.get(c)
            if other is not None and other is not agent:
                obs.robots[c] = other.id
            p = m.pheromone.read(x, y)
            if p > 0:
                obs.pheromone[c] = p
    return obs
