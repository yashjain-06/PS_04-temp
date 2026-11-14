"""Baseline vs ACO route comparison for the logistics page (owner: M3 + M4)."""
from flask import Blueprint, jsonify, request

from src.env.blueprint import BlueprintError, load_blueprint
from src.env.grid import Grid
from src.logistics.compare import compare_routes
from web.services.blueprints import safe_blueprint

bp = Blueprint("logistics", __name__, url_prefix="/api")
_CACHE: dict = {}


@bp.get("/logistics")
def logistics():
    try:
        name = safe_blueprint(request.args.get("blueprint", "blueprints/wall_with_opening.json"))
    except ValueError as e:
        return jsonify(error=str(e)), 404
    seed = int(request.args.get("seed", 1))
    key = (name, seed)
    if key not in _CACHE:
        try:
            b = load_blueprint(name)
        except BlueprintError as e:
            return jsonify(error=str(e)), 404
        grid = Grid(b.width, b.height, b.obstacles, b.depots)
        res = compare_routes(b, grid, seed=seed)
        rows = res.pop("rows")
        hit = [r for r in rows if r["baseline_hits_obstacle"]] or rows
        ex = max(hit, key=lambda r: r["baseline"] - r["optimal"]) if hit else None   # a pair where the baseline suffers
        res["example"] = ex and {k: ex[k] for k in ("src", "dst", "optimal", "baseline", "aco", "baseline_route", "aco_route")}
        res["site"] = {"grid": {"width": b.width, "height": b.height, "depth": 1},
                       "blueprint": [list(c) for c in b.cells], "depots": [list(d) for d in b.depots],
                       "obstacles": [list(o) for o in b.obstacles]}
        _CACHE[key] = res
    return jsonify(_CACHE[key])
