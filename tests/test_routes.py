from src.env.blueprint import load_blueprint
from src.env.grid import Grid
from src.logistics import baseline
from src.logistics.astar import shortest_path
from src.logistics.compare import compare_routes
from src.logistics.path_graph import PathGraph
from src.logistics.router import Router
from src.sim.seeding import make_rng


def site():
    bp = load_blueprint("blueprints/wall_with_opening.json")
    return bp, Grid(bp.width, bp.height, bp.obstacles, bp.depots)


def walkable(route, grid, src):
    cur = src
    for c in route:
        assert abs(c[0] - cur[0]) + abs(c[1] - cur[1]) == 1, "route has a jump"
        cur = c


def test_straight_route_reaches_goal_and_ignores_rocks():
    r = baseline.straight_route((0, 4), (9, 6))
    walkable(r, None, (0, 4))
    assert r[-1] == (9, 6) and any(c in {(5, y) for y in range(12)} for c in r)


def test_random_route_reaches_goal():
    r = baseline.random_route((0, 4), (9, 6), make_rng(1, "t"))
    assert r[-1] == (9, 6)


def test_baseline_and_aco_share_one_interface():
    bp, g = site()
    for use_aco in (False, True):
        router = Router(g, use_aco=use_aco, seed=1)
        route = router.get_route((0, 4), (9, 6))
        assert route and route[-1] == (9, 6) and router.get_route((3, 3), (3, 3)) == []
        walkable(route, g, (0, 4))


def test_aco_routes_avoid_rocks_and_are_near_optimal():
    bp, g = site()
    res = compare_routes(bp, g, seed=3)
    assert res["aco_obstacle_rate"] == 0.0 and res["baseline_obstacle_rate"] > 0.5
    assert res["aco_vs_optimal"] < 1.2 and res["aco_fallbacks"] == 0


def test_aco_respects_blocked_cells():
    bp, g = site()
    router = Router(g, use_aco=True, seed=1)
    free = router.get_route((0, 4), (9, 6))
    cut = {free[len(free) // 2]}
    detour = router.get_route((0, 4), (9, 6), blocked=cut)
    assert detour and detour[-1] == (9, 6) and not (set(detour) & cut)


def test_astar_is_shortest_and_none_when_unreachable():
    bp, g = site()
    graph = PathGraph(g)
    p = shortest_path(graph, (0, 4), (9, 6))
    assert p[-1] == (9, 6) and not any(c in g.obstacles for c in p)
    walled = {(x, y) for x in (8, 9) for y in range(12)}
    assert shortest_path(graph, (0, 4), (12, 6), blocked=walled) is None
