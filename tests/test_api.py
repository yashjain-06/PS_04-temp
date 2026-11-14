import json
from web.app import create_app


def client():
    return create_app().test_client()


def test_start_step_and_complete():
    c = client()
    snap = c.post("/api/start", json={"n_agents": 10, "seed": 1}).get_json()
    assert snap["tick"] == 0 and snap["metrics"]["accuracy"] == 0
    for _ in range(60):
        snap = c.post("/api/step", json={"n": 25}).get_json()
        if snap["metrics"]["complete"]:
            break
    assert snap["metrics"]["complete"] and snap["metrics"]["accuracy"] == 1.0
    assert {tuple(x) for x in snap["structure"]} == {tuple(x) for x in snap["blueprint"]}
    m = c.get("/api/metrics").get_json()
    assert m["complete"] and m["build_time"] == snap["tick"]


def test_snapshot_shape_matches_contract():
    c = client()
    snap = c.post("/api/start", json={"n_agents": 3}).get_json()
    for key in ("tick", "grid", "blueprint", "structure", "depots", "agents", "pheromone", "metrics"):
        assert key in snap
    a = snap["agents"][0]
    assert set(a) == {"id", "x", "y", "state", "carrying", "failed"}
    json.dumps(snap)   # JSON-safe


def test_failures_and_still_completes():
    c = client()
    c.post("/api/start", json={"n_agents": 20, "fail_rate": 0.3, "fail_at_tick": 10, "seed": 2})
    for _ in range(300):
        snap = c.post("/api/step", json={"n": 25}).get_json()
        if snap["metrics"]["complete"]:
            break
    assert snap["metrics"]["failed_agents"] == 6 and snap["metrics"]["complete"]


def test_bad_input_and_no_run():
    c = client()
    c.post("/api/reset")
    assert c.get("/api/state").status_code == 409
    assert c.post("/api/start", json={"n_agents": 0}).status_code == 400
    assert c.post("/api/start", json={"fail_rate": 2}).status_code == 400


def test_failure_tick_validation():
    assert client().post("/api/start", json={"fail_at_tick": 0}).status_code == 400


def test_results_endpoints():
    c = client()
    assert c.get("/api/results").status_code == 200
    assert c.get("/api/results/..%2Fsecret").status_code in (400, 404)
    assert c.get("/api/results/does_not_exist").status_code == 404


def test_experiments_page_and_results_roundtrip():
    from pathlib import Path
    c = client()
    page = c.get("/experiments")
    assert page.status_code == 200 and b"Experiments" in page.data
    path = Path("results/summary/zz_test_summary.csv")
    path.write_text("n_agents,fail_rate,use_aco,build_time_mean,exact_rate\n10,0.0,False,101.4,1.0\n")
    try:
        row = c.get("/api/results/zz_test_summary").get_json()[0]
        assert row["n_agents"] == 10 and row["fail_rate"] == 0.0 and row["use_aco"] is False
        assert "zz_test_summary" in c.get("/api/results").get_json()["summary"]
    finally:
        path.unlink()


def test_logistics_endpoint_and_page():
    c = client()
    assert c.get("/logistics").status_code == 200
    d = c.get("/api/logistics?blueprint=blueprints/wall_with_opening.json").get_json()
    assert d["aco_obstacle_rate"] == 0.0 and d["baseline_obstacle_rate"] > 0.5 and d["aco_vs_optimal"] < 1.2
    ex = d["example"]
    assert ex["aco_route"][-1] == ex["dst"] == ex["baseline_route"][-1] and d["convergence"]
    assert c.get("/api/logistics?blueprint=blueprints/nope.json").status_code == 404


def test_blueprint_editor_validate_save_and_run():
    from pathlib import Path
    c = client()
    good = {"name": "zz_test_bp", "width": 12, "height": 8, "depots": [[0, 0]], "obstacles": [[3, 3]],
            "cells": [[5, 4, 0], [6, 4, 0], [7, 4, 0]]}
    assert c.post("/api/blueprint/validate", json=good).get_json()["ok"] is True
    bad = c.post("/api/blueprint/validate", json={**good, "cells": [[3, 3, 0]]}).get_json()     # target on a rock
    assert bad["ok"] is False and "obstacle" in bad["error"]
    corridor = {"name": "x", "width": 8, "height": 4, "depots": [[0, 0]], "cells": [[2, 0, 0], [3, 0, 0]]}
    assert c.post("/api/blueprint/validate", json={**corridor, "obstacles": [[1, 1], [2, 1], [3, 1], [4, 1], [0, 1]]}).get_json()["ok"] is False
    assert c.post("/api/blueprint/save", json={**good, "name": "../evil"}).status_code == 400
    path = Path("blueprints/uploads/zz_test_bp.json")
    try:
        saved = c.post("/api/blueprint/save", json=good).get_json()["path"]
        assert path.exists() and saved in c.get("/api/blueprints").get_json()
        snap = c.post("/api/start", json={"blueprint": saved, "n_agents": 5}).get_json()
        for _ in range(60):
            snap = c.post("/api/step", json={"n": 20}).get_json()
            if snap["metrics"]["complete"]:
                break
        assert snap["metrics"]["complete"]
    finally:
        path.unlink(missing_ok=True)


def test_blueprint_paths_cannot_escape_the_blueprints_folder():
    c = client()
    for bad in ("../README.md", "/etc/passwd", "configs/default.yaml", "blueprints/../requirements.txt"):
        assert c.post("/api/start", json={"blueprint": bad}).status_code == 400, bad
        assert c.get("/api/blueprint?path=" + bad).status_code == 404, bad


def test_pso_depot_option_and_endpoint():
    c = client()
    r = c.get("/api/depots/optimize?blueprint=blueprints/wall_with_opening.json").get_json()
    assert r["fitness"] < r["original_fitness"] and r["fitness"] <= r["random_search_fitness"] and r["depots"]
    snap = c.post("/api/start", json={"n_agents": 5, "pso_depots": True}).get_json()
    assert [list(d) for d in snap["depots"]] == r["depots"] or len(snap["depots"]) >= 1
    assert c.get("/editor").status_code == 200


def test_ml_endpoints():
    c = client()
    d = c.get("/api/insights?blueprint=blueprints/wall_with_opening.json").get_json()
    assert d["aco"]["best_n_agents"] and len(d["aco"]["curve"]) == 10 and d["report"]["held_out_seed"]
    p = c.get("/api/predict?blueprint=blueprints/wall_with_opening.json&n_agents=10&use_aco=true").get_json()
    assert p["predicted_build_time"] > 0
    assert c.get("/api/predict?n_agents=0").status_code == 400
    assert c.get("/api/insights?blueprint=../README.md").status_code == 404
    assert c.get("/insights").status_code == 200


def test_each_visitor_gets_their_own_simulation():
    from web.app import create_app
    app = create_app()
    a, b = app.test_client(), app.test_client()            # separate cookie jars = two different visitors
    a.post("/api/start", json={"n_agents": 5, "blueprint": "blueprints/simple_wall.json"})
    b.post("/api/start", json={"n_agents": 12, "blueprint": "blueprints/u_shape.json"})
    a.post("/api/step", json={"n": 5})
    sa, sb = a.get("/api/state").get_json(), b.get("/api/state").get_json()
    assert len(sa["agents"]) == 5 and len(sb["agents"]) == 12 and sa["tick"] == 5 and sb["tick"] == 0
    b.post("/api/reset")
    assert a.get("/api/state").status_code == 200 and b.get("/api/state").status_code == 409   # b's reset did not touch a
    fresh = app.test_client()
    assert fresh.get("/api/state").status_code == 409        # a brand-new visitor starts with no run


def test_session_store_evicts_idle_and_caps_size():
    from web.services import session_store as ss
    s = ss.SessionStore()
    r1 = s.get("x")
    assert s.get("x") is r1 and s.get("y") is not r1
    old_cap = ss.MAX_SESSIONS
    try:
        ss.MAX_SESSIONS = 3
        for i in range(10):
            s.get(f"k{i}")
        assert len(s) <= 3
    finally:
        ss.MAX_SESSIONS = old_cap


def test_upload_cap_and_agent_limit():
    import web.api.blueprint_routes as br
    c = client()
    good = {"name": "zz_cap_bp", "width": 12, "height": 8, "depots": [[0, 0]], "cells": [[5, 4, 0], [6, 4, 0]]}
    old = br.MAX_UPLOADS
    try:
        br.MAX_UPLOADS = 0
        assert c.post("/api/blueprint/save", json=good).status_code == 429
    finally:
        br.MAX_UPLOADS = old
    assert c.post("/api/start", json={"n_agents": 61}).status_code == 400
