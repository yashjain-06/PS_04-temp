"""BFS reachability: do all unbuilt target cells stay reachable from a depot? (owner: M1)

This is the 'never close a gap that would later be unreachable' rule from the TERMES idea.
Robots can walk on every cell that is not an obstacle and not yet built (unbuilt targets are ground).
"""
from __future__ import annotations

from collections import deque


def all_reachable(grid, depots, blocked, must_reach) -> bool:
    """True if every cell in `must_reach` can be reached from a depot without crossing `blocked`."""
    need = set(must_reach)
    if not need:
        return True
    seen = {d for d in depots if d not in blocked}
    q = deque(seen)
    need -= seen
    while q and need:
        cur = q.popleft()
        for n in grid.neighbors4(cur):
            if n not in seen and n not in blocked:
                seen.add(n)
                need.discard(n)
                q.append(n)
    return not need
