"""Surrogate predictions for the insights page (owner: M4). Offline analysis only; never controls robots."""
import json

from flask import Blueprint, jsonify, request

from web.services.blueprints import safe_blueprint

bp = Blueprint("ml", __name__, url_prefix="/api")


def _model_ready():
    from src.ml.surrogate import DATA_PATH, MODEL_PATH
    return MODEL_PATH.exists() or DATA_PATH.exists()          # a missing/incompatible model is retrained from the data


@bp.get("/insights")
def insights():
    try:
        name = safe_blueprint(request.args.get("blueprint", "blueprints/wall_with_opening.json"))
    except ValueError as e:
        return jsonify(error=str(e)), 404
    if not _model_ready():
        return jsonify(error="surrogate not trained: run scripts/make_surrogate_data.py then scripts/train_surrogate.py"), 503
    from src.ml.surrogate import REPORT_PATH, curve, recommend
    return jsonify({"blueprint": name,
                    "baseline": {"curve": curve(name, False), **{k: v for k, v in recommend(name, False).items() if k != "curve"}},
                    "aco": {"curve": curve(name, True), **{k: v for k, v in recommend(name, True).items() if k != "curve"}},
                    "report": json.loads(REPORT_PATH.read_text()) if REPORT_PATH.exists() else None})


@bp.get("/predict")
def predict():
    if not _model_ready():
        return jsonify(error="surrogate not trained"), 503
    try:
        name = safe_blueprint(request.args.get("blueprint", "blueprints/wall_with_opening.json"))
        n = int(request.args.get("n_agents", 10))
        if not 1 <= n <= 100:
            raise ValueError("n_agents must be 1..100")
    except ValueError as e:
        return jsonify(error=str(e)), 400
    from src.ml.surrogate import predict as p
    aco = request.args.get("use_aco", "false").lower() == "true"
    return jsonify(predicted_build_time=round(p(n, aco, name), 1), n_agents=n, use_aco=aco)
