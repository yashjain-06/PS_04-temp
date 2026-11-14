"""Purely local movement helpers (owner: M2): greedy detours and random walks."""
from __future__ import annotations


def free_neighbors(a) -> list:
    m = a.model
    return [n for n in m.grid.neighbors4((a.x, a.y)) if m.cell_status(n) == "free"]


def _dist(c, g) -> int:
    return abs(c[0] - g[0]) + abs(c[1] - g[1])


DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1)]          # clockwise: east, south, west, north


def _turn(d, k):
    return DIRS[(DIRS.index(d) + k) % 4]


def start_follow(a, nxt, goal) -> bool:
    """Hit an obstacle ahead: start following its contour (random hand), remember how far from goal we were."""
    pos = (a.x, a.y)
    bd = (nxt[0] - pos[0], nxt[1] - pos[1])
    hand = 1 if a.rng.random() < 0.5 else -1
    a.follower.reset()
    a.follow = {"goal": goal, "hand": hand, "h": _turn(bd, -hand), "d0": _dist(pos, goal), "steps": 0}
    return follow_step(a)


def follow_step(a) -> bool:
    """Wall-following: keep the obstacle on one side, turning around corners (Bug-style, purely local)."""
    f, m = a.follow, a.model
    f["steps"] += 1
    if f["steps"] > 200:                                  # hopeless: random walk and start over
        a.follow, a.wander = None, 5
        return False
    for k in (f["hand"], 0, -f["hand"], 2):               # hug the obstacle side first
        d = _turn(f["h"], k)
        c = (a.x + d[0], a.y + d[1])
        if m.cell_status(c) == "free":
            f["h"] = d
            m.move_agent(a, c)
            return True
    return False


def detour(a, goal) -> bool:
    """No route is known: step greedily toward goal (not straight back)."""
    a.follower.reset()
    opts = free_neighbors(a)
    nofwd = [c for c in opts if c != a.last] or opts
    if not nofwd:
        return False
    best = min(_dist(c, goal) for c in nofwd)
    ties = [c for c in nofwd if _dist(c, goal) == best]
    a.model.move_agent(a, ties[int(a.rng.integers(len(ties)))])
    return True


def random_step(a) -> bool:
    opts = free_neighbors(a)
    nofwd = [c for c in opts if c != a.last] or opts
    if not nofwd:
        return False
    a.model.move_agent(a, nofwd[int(a.rng.integers(len(nofwd)))])
    return True
