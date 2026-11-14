"""Keeps a robot's current route and replans when it is stale (owner: M3 + M2)."""
from __future__ import annotations


class RouteFollower:
    def __init__(self):
        self.goal = None
        self.route: list = []

    def reset(self) -> None:
        self.goal, self.route = None, []

    def next_cell(self, router, pos, goal, blocked=()):
        """Next cell toward `goal`, replanning if the goal changed or the route no longer starts next to pos."""
        stale = (self.goal != goal or not self.route
                 or abs(self.route[0][0] - pos[0]) + abs(self.route[0][1] - pos[1]) != 1
                 or any(c in blocked for c in self.route))
        if stale:
            self.goal = goal
            self.route = list(router.get_route(pos, goal, blocked))
        return self.route[0] if self.route else None

    def advance(self) -> None:
        if self.route:
            self.route.pop(0)
