import json
from src.logistics.pso import optimize_depots
from src.env.blueprint import load_blueprint
from src.env.grid import Grid
from src.ml import surrogate
from src.ml.dataset import featurize


def test_features_are_finite_and_aco_flag_changes_them():
    a, b = featurize(10, False, "blueprints/wall_with_opening.json"), featurize(10, True, "blueprints/wall_with_opening.json")
    assert a != b and all(v == v and abs(v) < 1e6 for v in a + b)


def test_surrogate_reports_good_heldout_accuracy():
    rep = json.loads(surrogate.REPORT_PATH.read_text())
    h = rep["held_out_seed"]
    assert h["gbr"]["r2"] > 0.8 and h["gbr"]["mae_ticks"] < h["predict_mean_baseline_mae"] / 2
    assert "leave_one_blueprint_out" in rep                     # the weaker, honest result is reported too


def test_predictions_are_sensible_and_recommendation_is_in_range():
    bp = "blueprints/wall_with_opening.json"
    fast, slow = surrogate.predict(10, True, bp), surrogate.predict(10, False, bp)
    assert 0 < fast < slow                                       # ACO is predicted faster at 10 agents, as measured
    r = surrogate.recommend(bp, True)
    assert 5 <= r["best_n_agents"] <= 50 and r["predicted_build_time"] > 0


def test_pso_beats_original_depots_and_random_search():
    bp = load_blueprint("blueprints/wall_with_opening.json")
    r = optimize_depots(bp, Grid(bp.width, bp.height, bp.obstacles, bp.depots), seed=2)
    assert r["fitness"] < r["original_fitness"] and r["fitness"] <= r["random_search_fitness"]
    assert r["history"] == sorted(r["history"], reverse=True)    # global best never gets worse
    assert all(tuple(d) not in bp.targets and tuple(d) not in set(bp.obstacles) for d in r["depots"])


def test_pso_depots_make_the_simulated_build_faster_and_still_exact():
    from src.experiments import metrics as M
    from src.sim.model import build_model
    bp = load_blueprint("blueprints/wall_with_opening.json")
    pso = optimize_depots(bp, Grid(bp.width, bp.height, bp.obstacles, bp.depots), seed=1)["depots"]
    t = {}
    for label, dep in (("orig", None), ("pso", pso)):
        m = build_model(blueprint="blueprints/wall_with_opening.json", n_agents=10, seed=1, depots=dep)
        while not m.build_complete() and m.tick < 3000:
            m.step()
        assert m.build_complete() and M.is_exact(m.structure_cells(), m.blueprint_cells())
        t[label] = m.tick
    assert t["pso"] < t["orig"]


def test_model_retrains_if_the_saved_file_is_unreadable():
    import shutil
    from pathlib import Path
    keep = Path(str(surrogate.MODEL_PATH) + ".bak")
    shutil.copy(surrogate.MODEL_PATH, keep)
    try:
        surrogate.MODEL_PATH.write_bytes(b"not a pickle")          # simulates a scikit-learn version mismatch
        surrogate._MODEL = None
        v = surrogate.predict(10, True, "blueprints/wall_with_opening.json")
        assert 20 < v < 300
    finally:
        shutil.move(str(keep), surrogate.MODEL_PATH)
        surrogate._MODEL = None
