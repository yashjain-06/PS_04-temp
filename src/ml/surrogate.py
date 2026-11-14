"""Build-time surrogate: predicts ticks to finish from (agents, routing, blueprint) (owner: M4).

This is an OFFLINE ANALYSIS TOOL trained on this project's own simulation runs. It never controls a robot,
so the swarm stays decentralised. Quality is reported on held-out data, not on the training set.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score

from src.ml.dataset import featurize, load_dataset

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "models" / "surrogate.joblib"
REPORT_PATH = ROOT / "results" / "summary" / "surrogate_report.json"


def _gbr():
    return GradientBoostingRegressor(n_estimators=200, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=0)


def _fit(X, y):
    """Fit on log(build time): build times are positive and skewed."""
    return _gbr().fit(X, np.log(y))


def _eval(m, X, y):
    p = np.exp(m.predict(X))
    return {"r2": round(float(r2_score(y, p)), 3), "mae_ticks": round(float(mean_absolute_error(y, p)), 1), "n": int(len(y))}


def train(csv_path, save=True) -> dict:
    X, y, groups, seeds = load_dataset(csv_path)
    report = {"rows": int(len(y)), "model": "GradientBoostingRegressor on log(build_time)"}
    test = seeds == seeds.max()                                              # held-out seed
    report["held_out_seed"] = {"gbr": _eval(_fit(X[~test], y[~test]), X[test], y[test])}
    ridge = Ridge(alpha=1.0).fit(X[~test], np.log(y[~test]))
    report["held_out_seed"]["ridge_baseline"] = {"r2": round(float(r2_score(y[test], np.exp(ridge.predict(X[test])))), 3),
                                                  "mae_ticks": round(float(mean_absolute_error(y[test], np.exp(ridge.predict(X[test])))), 1)}
    report["held_out_seed"]["predict_mean_baseline_mae"] = round(float(np.abs(y[test] - y[~test].mean()).mean()), 1)
    loo = {}                                                                 # leave one blueprint out: unseen site
    for g in sorted(set(groups)):
        t = groups == g
        loo[g] = _eval(_fit(X[~t], y[~t]), X[t], y[t])
    report["leave_one_blueprint_out"] = loo
    model = _fit(X, y)                                                       # final model uses all data
    if save:
        MODEL_PATH.parent.mkdir(exist_ok=True)
        joblib.dump(model, MODEL_PATH)
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=1))
    return report


_MODEL = None
DATA_PATH = ROOT / "results" / "raw" / "surrogate_data.csv"


def _load_model():
    """Load the saved model; if it was pickled by a different scikit-learn version (or is missing/corrupt),
    retrain from the saved simulation data instead (takes about a second)."""
    try:
        return joblib.load(MODEL_PATH)
    except Exception:                                                        # noqa: BLE001
        X, y, _, _ = load_dataset(DATA_PATH)
        return _fit(X, y)


def predict(n_agents: int, use_aco: bool, blueprint: str) -> float:
    global _MODEL
    if _MODEL is None:
        _MODEL = _load_model()
    return float(np.exp(_MODEL.predict(np.array([featurize(n_agents, use_aco, blueprint)]))[0]))


def curve(blueprint: str, use_aco: bool, counts=range(5, 51, 5)) -> list:
    return [{"n_agents": n, "predicted_build_time": round(predict(n, use_aco, blueprint), 1)} for n in counts]


def recommend(blueprint: str, use_aco: bool) -> dict:
    c = curve(blueprint, use_aco, range(5, 51))
    best = min(c, key=lambda r: r["predicted_build_time"])
    return {"blueprint": blueprint, "use_aco": use_aco, "best_n_agents": best["n_agents"],
            "predicted_build_time": best["predicted_build_time"], "curve": c[::5]}
