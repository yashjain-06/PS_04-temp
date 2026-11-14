from src.agents.collision import priority, should_yield
from src.sim.model import build_model


class A:
    def __init__(self, i, carrying): self.id, self.carrying = i, carrying


def test_carrying_robot_has_right_of_way_then_lower_id():
    assert priority(A(5, True)) < priority(A(1, False))
    assert priority(A(1, True)) < priority(A(2, True))


def test_low_priority_yields_fast_high_priority_waits():
    low, high = A(9, False), A(1, True)
    assert should_yield(low, high, waited=1, patience=4)
    assert not should_yield(high, low, waited=1, patience=4) and should_yield(high, low, waited=4, patience=4)


def test_one_robot_per_cell_always():
    for aco in (False, True):
        m = build_model(blueprint="blueprints/wall_with_opening.json", n_agents=30, use_aco=aco, seed=5)
        for _ in range(150):
            m.step()
            pos = [(a.x, a.y) for a in m.agents]
            assert len(pos) == len(set(pos))
            assert all(m.grid.passable(x, y) and (x, y) not in m.rules.structure.cells for x, y in pos)
            assert len(m.occupancy) == len(m.agents)
