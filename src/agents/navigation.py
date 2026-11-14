"""Follow a route one cell per tick, handling blockers locally (owner: M2)."""
from __future__ import annotations

from src.agents import collision, deadlock, local_movement


def navigate(a, goal) -> str:
    """Advance one step toward goal. Returns 'arrived' | 'moved' | 'waited' | 'detoured'."""
    m, pos = a.model, (a.x, a.y)
    if pos == goal:
        return "arrived"
    f = a.follow
    if f and f["goal"] != goal:
        a.follow, f = None, None
    nxt = a.follower.next_cell(m.router, pos, goal, a.seen_built)
    if f:                                                    # following an obstacle: leave once we are closer than at the hit point
        closer = abs(pos[0] - goal[0]) + abs(pos[1] - goal[1]) < f["d0"]
        if nxt is not None and closer and m.cell_status(nxt) == "free":
            a.follow = None
        else:
            return "detoured" if local_movement.follow_step(a) else "waited"
    if nxt is None:                                          # no route known: move greedily
        return "detoured" if local_movement.detour(a, goal) else "waited"
    status = m.cell_status(nxt)
    if status == "free":
        m.move_agent(a, nxt)
        a.follower.advance()
        a.blocked_ticks, a.follow = 0, None
        return "moved"
    if status == "robot":
        other = m.occupancy[nxt]
        a.blocked_ticks += 1
        m.congestion.blocked_ticks += 1
        if collision.should_yield(a, other, a.blocked_ticks, m.patience):
            return "detoured" if deadlock.backoff(a, goal) else "waited"
        return "waited"
    return "detoured" if local_movement.start_follow(a, nxt, goal) else "waited"     # block, rock or failed robot
