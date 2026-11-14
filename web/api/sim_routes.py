"""Simulation control endpoints (owner: M4)."""
from pathlib import Path

from flask import Blueprint, jsonify, request

from src.utils.config import load_config
from src.env.blueprint import load_blueprint
from src.env.grid import Grid
from src.logistics.pso import optimize_depots
from web.services.blueprints import list_blueprints, safe_blueprint
from web.services.session_store import get_runner

bp = Blueprint("sim", __name__, url_prefix="/api")
ROOT = Path(__file__).resolve().parents[2]


_PSO: dict = {}


def pso_depots(blueprint: str, seed: int) -> dict:
    key = (blueprint, seed)
    if key not in _PSO:
        b = load_blueprint(blueprint)
        _PSO[key] = optimize_depots(b, Grid(b.width, b.height, b.obstacles, b.depots), seed=seed)
    return _PSO[key]


@bp.get("/depots/optimize")
def depots_optimize():
    try:
        name = safe_blueprint(request.args.get("blueprint", "blueprints/wall_with_opening.json"))
    except ValueError as e:
        return jsonify(error=str(e)), 404
    return jsonify(pso_depots(name, int(request.args.get("seed", 1))))


@bp.get("/blueprints")
def blueprints_endpoint():
    return jsonify(list_blueprints())


@bp.get("/config")
def get_config():
    return jsonify(load_config())


@bp.post("/start")
def start():
    body = request.get_json(silent=True) or {}
    d = load_config()
    try:
        blueprint = safe_blueprint(body.get("blueprint", d["simulation"]["blueprint"]))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    params = {
        "blueprint": blueprint,
        "n_agents": int(body.get("n_agents", d["simulation"]["n_agents"])),
        "fail_rate": float(body.get("fail_rate", d["failure"]["rate"])),
        "use_aco": bool(body.get("use_aco", d["logistics"]["use_aco"])),
        "seed": int(body.get("seed", d["simulation"]["seed"])),
        "fail_at_tick": int(body.get("fail_at_tick", d["failure"]["at_tick"])),
        "max_ticks": int(d["simulation"]["max_ticks"]),
    }
    if not (1 <= params["n_agents"] <= 60):
        return jsonify(error="n_agents must be 1..60"), 400
    if params["fail_at_tick"] < 1:
        return jsonify(error="fail_at_tick must be >= 1"), 400
    if not (0.0 <= params["fail_rate"] <= 1.0):
        return jsonify(error="fail_rate must be 0..1"), 400
    if body.get("pso_depots"):                      # let PSO choose the depot positions for this blueprint
        params["depots"] = pso_depots(blueprint, params["seed"])["depots"]
    return jsonify(get_runner().start(params))


@bp.post("/step")
def step():
    n = int((request.get_json(silent=True) or {}).get("n", 1))
    snap = get_runner().step(n)
    return (jsonify(snap), 200) if snap else (jsonify(error="no run started"), 409)


@bp.get("/state")
def state():
    snap = get_runner().state()
    return (jsonify(snap), 200) if snap else (jsonify(error="no run started"), 409)


@bp.post("/pause")
def pause():
    get_runner().pause()
    return jsonify(ok=True)


@bp.post("/resume")
def resume():
    get_runner().resume()
    return jsonify(ok=True)


@bp.post("/reset")
def reset():
    get_runner().reset()
    return jsonify(ok=True)


@bp.get("/metrics")
def metrics():
    return jsonify(get_runner().metrics())
