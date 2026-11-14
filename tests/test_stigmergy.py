from src.agents import stigmergy
from src.agents.stigmergy import PheromoneField
from src.sim.model import build_model


def test_deposit_read_evaporate_and_cap():
    f = PheromoneField(5, 5, evaporation=0.5)
    f.deposit(2, 2, 0.8); f.deposit(2, 2, 0.8)
    assert f.read(2, 2) == 1.0                                   # capped
    f.evaporate()
    assert abs(f.read(2, 2) - 0.5) < 1e-9
    for _ in range(20):
        f.evaporate()
    assert f.read(2, 2) == 0.0 and f.read(99, 99) == 0.0          # fades to zero, out-of-range is safe


def test_module_level_api_and_placement_leaves_a_mark():
    m = build_model(blueprint="blueprints/simple_wall.json", n_agents=10, seed=1)
    while m.blocks_placed == 0:
        m.step()
    stigmergy.set_active(m.pheromone)
    assert any(stigmergy.read(x, y) > 0 for y in range(m.grid.height) for x in range(m.grid.width))
    stigmergy.deposit(0, 0, 0.3); assert stigmergy.read(0, 0) > 0
    stigmergy.evaporate()
