"""Builder robot (owner: M2): plain state + the FSM in fsm.py. No access to the model's task list."""
from __future__ import annotations

from src.agents import fsm
from src.agents.agent_state import agent_state
from src.logistics.route_follower import RouteFollower
from src.sim.seeding import make_rng


class Builder:
    def __init__(self, uid: int, x: int, y: int, model, seed: int = 0):
        self.id, self.x, self.y, self.model = uid, x, y, model
        self.state, self.carrying, self.failed, self.relocated = "seek", False, False, False
        self.rng = make_rng(seed, f"agent{uid}")
        self.follower = RouteFollower()
        self.seen_built: set = set()      # memory: built cells this robot has itself observed
        self.site = None
        self.depot = None                 # depot chosen for the current trip
        self.commit = None                # committed goal while carrying: {site, goal, age}
        self.last = None
        self.follow = None                # wall-following state while going around an obstacle
        self.blocked_ticks = self.wander = self.load_timer = self.active_ticks = 0

    def step(self) -> None:
        fsm.step(self)

    def state_dict(self) -> dict:
        return agent_state(self)
