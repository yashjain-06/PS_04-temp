"""Random back-off for robots blocked by other robots (owner: M2)."""
from __future__ import annotations

from src.agents.local_movement import free_neighbors


def backoff(a, goal) -> bool:
    """Step sideways to a random free neighbour (never straight back) and drop the old route."""
    a.follower.reset()
    a.blocked_ticks = 0
    opts = free_neighbors(a)
    nofwd = [c for c in opts if c != a.last] or opts
    if not nofwd:
        return False
    a.model.move_agent(a, nofwd[int(a.rng.integers(len(nofwd)))])
    return True
