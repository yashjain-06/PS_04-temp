from src.experiments import metrics as M
from src.sim.model import build_model


def run(bp, n, aco, seed, cap=3000):
    m = build_model(blueprint=f"blueprints/{bp}.json", n_agents=n, use_aco=aco, seed=seed)
    while not m.build_complete() and m.tick < cap:
        m.step()
    return m


def test_thirty_and_fifty_robots_finish_exactly():
    for n in (30, 50):
        m = run("wall_with_opening", n, False, seed=2)
        assert m.build_complete() and M.is_exact(m.structure_cells(), m.blueprint_cells()), n


def test_every_blueprint_finishes_exactly_in_both_routing_modes():
    for bp in ("simple_wall", "wall_with_opening", "double_wall", "u_shape"):
        for aco in (False, True):
            m = run(bp, 10, aco, seed=1)
            assert m.build_complete() and M.is_exact(m.structure_cells(), m.blueprint_cells()), (bp, aco)


def test_no_block_is_ever_unsupported():
    m = build_model(blueprint="blueprints/u_shape.json", n_agents=20, seed=4)
    while not m.build_complete() and m.tick < 3000:
        m.step()
        for (x, y) in m.rules.structure.cells:
            assert (x, y) in m.rules.seeds or any(n in m.rules.structure.cells for n in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)))
    assert m.build_complete()
