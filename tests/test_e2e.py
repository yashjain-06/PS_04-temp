"""First-integration check: runs against FakeModel now, real model once USE_REAL_MODEL = True."""
from src.experiments.runner import run_one


def test_ten_agents_build_wall_with_opening_exactly():
    r = run_one({"blueprint": "blueprints/wall_with_opening.json", "n_agents": 10, "fail_rate": 0.0,
                 "use_aco": False, "seed": 42, "fail_at_tick": 200, "max_ticks": 3000})
    assert r.completed and r.exact and r.extra_cells == 0 and r.accuracy == 1.0


def test_simple_wall_and_aco_flag_accepted():
    for bp in ("blueprints/simple_wall.json", "blueprints/wall_with_opening.json"):
        for aco in (False, True):
            r = run_one({"blueprint": bp, "n_agents": 10, "fail_rate": 0.0, "use_aco": aco,
                         "seed": 7, "fail_at_tick": 200, "max_ticks": 3000})
            assert r.completed and r.exact
