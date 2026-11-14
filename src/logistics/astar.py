"""A* shortest path on the site graph (owner: M3). Used as the optimality reference and ACO fallback."""
from __future__ import annotations

import heapq


def shortest_path(graph, src, dst, blocked=frozenset()):
    """Return path as a list of cells excluding src and including dst; [] if src == dst; None if unreachable."""
    if src == dst:
        return []
    h = lambda c: abs(c[0] - dst[0]) + abs(c[1] - dst[1])                # noqa: E731
    open_, best, came = [(h(src), 0, src)], {src: 0}, {}
    while open_:
        _, g, cur = heapq.heappop(open_)
        if cur == dst:
            path = []
            while cur != src:
                path.append(cur)
                cur = came[cur]
            return path[::-1]
        if g > best.get(cur, 1e9):
            continue
        for n in graph.neighbors(cur):
            if n in blocked:
                continue
            ng = g + 1
            if ng < best.get(n, 1e9):
                best[n], came[n] = ng, cur
                heapq.heappush(open_, (ng + h(n), ng, n))
    return None
