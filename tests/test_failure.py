from src.sim.events import EventLog
from src.sim.failure import fail_agents
from src.sim.fake_model import FakeModel
from src.experiments.runner import run_one
import pytest


class Obj:                       # object-style agent, like M2's Builder
    def __init__(self, i): self.id, self.failed = i, False


class M:
    def __init__(self, agents): self.agents, self.events = agents, EventLog()


def test_counts_and_determinism():
    ids1 = fail_agents(M([Obj(i) for i in range(10)]), 0.3, tick=5, seed=1)
    ids2 = fail_agents(M([Obj(i) for i in range(10)]), 0.3, tick=5, seed=1)
    assert len(ids1) == 3 and ids1 == ids2


def test_only_active_agents_and_events():
    m = M([Obj(i) for i in range(10)])
    first = fail_agents(m, 0.3, 5, 1)
    second = fail_agents(m, 0.3, 6, 1)
    assert not set(first) & set(second)                    # never re-fails a dead agent
    assert sum(a.failed for a in m.agents) == 6
    assert m.events.count("failed") == 6


def test_rate_edges_and_dict_agents():
    m = M([{"id": i, "failed": False} for i in range(4)])
    assert fail_agents(m, 0.0) == []
    assert len(fail_agents(m, 1.0)) == 4
    with pytest.raises(ValueError):
        fail_agents(m, 1.5)


def test_build_completes_at_30_percent_failure():
    for seed in (1, 2):
        r = run_one({"blueprint": "blueprints/wall_with_opening.json", "n_agents": 20, "fail_rate": 0.3,
                     "use_aco": False, "seed": seed, "fail_at_tick": 30, "max_ticks": 3000})
        assert r.completed and r.exact and r.extra_cells == 0


def test_failed_agents_do_not_move_or_work():
    m = FakeModel(n_agents=10, fail_rate=0.5, fail_at_tick=5, seed=1)
    for _ in range(5):
        m.step()
    frozen = {a["id"]: (a["x"], a["y"]) for a in m.agents if a["failed"]}
    ticks = {a["id"]: a["active_ticks"] for a in m.agents if a["failed"]}
    for _ in range(10):
        m.step()
    assert frozen and all((a["x"], a["y"]) == frozen[a["id"]] for a in m.agents if a["failed"])
    assert all(a["active_ticks"] == ticks[a["id"]] for a in m.agents if a["failed"])


def test_real_model_survives_failures_and_failed_robots_stay_put():
    from src.sim.model import build_model
    for seed in (1, 2, 3):
        m = build_model(blueprint="blueprints/wall_with_opening.json", n_agents=20, fail_rate=0.3, fail_at_tick=25, seed=seed)
        while m.tick < 26:
            m.step()
        dead = {a.id: (a.x, a.y) for a in m.agents if a.failed}
        assert len(dead) == 6
        while not m.build_complete() and m.tick < 3000:
            m.step()
        assert m.build_complete() and all((a.x, a.y) == dead[a.id] for a in m.agents if a.failed)
        assert not any(p in m.rules.targets or m.depots.is_depot(p) for p in dead.values())   # never block the build
        assert m.events.count("failed") == 6


def test_dead_robots_never_seal_the_site():
    from src.env.reachability import all_reachable
    from src.sim.model import build_model
    for seed in range(1, 6):
        m = build_model(blueprint="blueprints/u_shape.json", n_agents=30, fail_rate=0.3, fail_at_tick=20, seed=seed)
        for _ in range(25):
            m.step()
        dead = {(a.x, a.y) for a in m.agents if a.failed}
        built = m.rules.structure.cells
        assert all_reachable(m.grid, m.depots.positions, built | dead, m.rules.targets - built), seed
