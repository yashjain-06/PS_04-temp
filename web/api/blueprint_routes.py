"""Blueprint editor API: load, validate, save (owner: M1 + M4)."""
import json

from flask import Blueprint, jsonify, request

from src.env.blueprint import BlueprintError, load_blueprint, parse_blueprint
from src.env.rules import RuleSet
from src.env.rules_compiler import UnbuildableError
from web.services.blueprints import BP_DIR, NAME_OK, ROOT, safe_blueprint

bp = Blueprint("blueprint_editor", __name__, url_prefix="/api/blueprint")
MAX_SIDE = 40
MAX_UPLOADS = 100          # protects the disk when the site is public


def _check(d: dict):
    if not (4 <= int(d.get("width", 0)) <= MAX_SIDE and 4 <= int(d.get("height", 0)) <= MAX_SIDE):
        raise BlueprintError(f"width and height must be between 4 and {MAX_SIDE}")
    b = parse_blueprint(d, d.get("name", "custom"))
    RuleSet(b).check_buildable(trials=5, seed=0)          # reject dead ends in the rules
    return b


@bp.get("")
def get_blueprint():
    try:
        return jsonify(load_blueprint(safe_blueprint(request.args.get("path", ""))).to_json())
    except (ValueError, BlueprintError) as e:
        return jsonify(error=str(e)), 404


@bp.post("/validate")
def validate():
    try:
        b = _check(request.get_json(silent=True) or {})
        rs = RuleSet(b)
        return jsonify(ok=True, targets=len(b.cells), seeds=[list(s) for s in sorted(rs.seeds)])
    except (BlueprintError, UnbuildableError, TypeError, ValueError) as e:
        return jsonify(ok=False, error=str(e)), 200


@bp.post("/save")
def save():
    d = request.get_json(silent=True) or {}
    name = str(d.get("name", ""))
    if not NAME_OK.match(name):
        return jsonify(error="name must be 1-40 letters, digits, _ or -"), 400
    try:
        b = _check({**d, "name": name})
    except (BlueprintError, UnbuildableError, TypeError, ValueError) as e:
        return jsonify(error=str(e)), 400
    (BP_DIR / "uploads").mkdir(exist_ok=True)
    if not (BP_DIR / "uploads" / f"{name}.json").exists() and len(list((BP_DIR / "uploads").glob("*.json"))) >= MAX_UPLOADS:
        return jsonify(error="upload limit reached"), 429
    path = BP_DIR / "uploads" / f"{name}.json"
    path.write_text(json.dumps(b.to_json(), indent=1))
    return jsonify(path=path.relative_to(ROOT).as_posix())
