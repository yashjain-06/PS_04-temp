"""Finite-state machine of a builder robot (owner: M2).

seek   : empty, heading to a depot (start of the run)
carry  : holding a block, looking for a legal site (uses ONLY local observation + memory)
place  : standing next to a legal site, placing the block (one tick)
return : empty again after placing, heading back to a depot
No robot is ever told what to build: it picks sites it can sense and the rules allow.
"""
from __future__ import annotations

from src.agents.local_movement import free_neighbors, random_step
from src.agents.navigation import navigate
from src.agents.sensing import observe

STATES = ("seek", "carry", "place", "return")


def _manhattan(a, b) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def step(a) -> None:
    obs = observe(a, a.model.sensing_radius)
    a.seen_built |= obs.built                                # memory of blocks this robot has itself seen
    if a.wander > 0:                                         # short random walk to escape local minima
        a.wander -= 1
        if random_step(a):
            return
    if a.state in ("seek", "return"):
        _to_depot(a)
    elif a.state == "carry":
        _carry(a, obs)
    elif a.state == "place":
        _place(a)


def _to_depot(a) -> None:
    m, pos = a.model, (a.x, a.y)
    if a.depot is None:                                      # choose once per trip so the goal (and route) stays stable
        a.depot = m.depots.nearest(pos, a.rng)
    depot = a.depot
    if pos == depot:
        a.load_timer += 1
        if a.load_timer >= m.load_time:
            a.load_timer, a.carrying, a.state, a.depot = 0, True, "carry", None
            a.follower.reset()
        return
    if _manhattan(pos, depot) <= 2:
        m.congestion.depot_queue_ticks += 1
    navigate(a, depot)


def _in_view(a, cell) -> bool:
    return max(abs(cell[0] - a.x), abs(cell[1] - a.y)) <= a.model.sensing_radius


def _carry(a, obs) -> None:
    """Find a legal site. Robots COMMIT to a goal until they arrive, it is taken, or it times out,
    so they do not flip between goals while going around an obstacle."""
    m, pos = a.model, (a.x, a.y)
    ok = [c for c in obs.targets_unbuilt if c != pos and c not in obs.robots and m.rules.can_place(*c)]

    adjacent = [c for c in ok if _manhattan(c, pos) == 1]
    if adjacent:                                             # legal site right next to me: place it
        a.site = adjacent[int(a.rng.integers(len(adjacent)))]
        a.state, a.commit = "place", None
        return

    c = a.commit
    if c:
        c["age"] += 1
        taken = _in_view(a, c["site"]) and c["site"] not in ok
        if c["age"] > 150 or pos == c["goal"] or taken or c["site"] in a.seen_built:
            a.commit = c = None
    if c:
        navigate(a, c["goal"])
        return

    if ok:                                                   # legal site in view: commit to a stand cell next to it
        site = min(ok, key=lambda t: (_manhattan(t, pos), t))
        stands = [n for n in m.grid.neighbors4(site) if m.cell_status(n) == "free"]
        if stands:
            goal = min(stands, key=lambda t: (_manhattan(t, pos), t))
            a.commit = {"site": site, "goal": goal, "age": 0}
            navigate(a, goal)
            return
    if _follow_pheromone(a, obs):                            # recent construction nearby: stay close
        return
    far = [t for t in m.rules.targets if t not in a.seen_built and not _in_view(a, t)]
    if far:                                                  # commit to the nearest cell I do not know to be built
        t = min(far, key=lambda t: (_manhattan(t, pos), t))
        a.commit = {"site": t, "goal": t, "age": 0}
        navigate(a, t)
        return
    random_step(a)                                           # waiting for the frontier to move: mill about


def _follow_pheromone(a, obs) -> bool:
    m = a.model
    here = m.pheromone.read(a.x, a.y)
    best, best_val = None, max(here, m.pheromone_threshold)
    for n in free_neighbors(a):
        v = obs.pheromone.get(n, 0.0)
        if v > best_val:
            best, best_val = n, v
    if best is None:
        return False
    m.move_agent(a, best)
    a.follower.reset()
    return True


def _place(a) -> None:
    m = a.model
    if a.site is not None and _manhattan(a.site, (a.x, a.y)) == 1 and m.try_place(a, a.site):
        a.carrying, a.state, a.site, a.commit = False, "return", None, None
        a.follower.reset()
    else:
        a.state, a.site = "carry", None
