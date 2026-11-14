from src.sim.model import build_model


def test_observation_never_leaves_the_radius():
    m = build_model(blueprint="blueprints/u_shape.json", n_agents=15, seed=3)
    from src.agents.sensing import observe
    for _ in range(80):
        m.step()
        for a in m.agents:
            r = m.sensing_radius
            obs = observe(a, r)
            for (x, y) in obs.cells_seen():
                assert max(abs(x - a.x), abs(y - a.y)) <= r, (a.id, (x, y), (a.x, a.y))


def test_robot_memory_only_holds_cells_it_actually_saw():
    m = build_model(blueprint="blueprints/wall_with_opening.json", n_agents=10, seed=1)
    for _ in range(60):
        m.step()
    assert all(c in m.rules.structure.cells for a in m.agents for c in a.seen_built)   # never invents blocks
    assert any(len(a.seen_built) < len(m.rules.structure) for a in m.agents) or len(m.rules.structure) == 0


def test_observation_includes_other_robots_but_not_self():
    m = build_model(blueprint="blueprints/simple_wall.json", n_agents=10, seed=1)
    from src.agents.sensing import observe
    a = m.agents[0]
    obs = observe(a, 3)
    assert (a.x, a.y) not in obs.robots and all(i != a.id for i in obs.robots.values())
