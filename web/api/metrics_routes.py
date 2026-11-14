"""Serve experiment CSVs as JSON for the charts (owner: M4)."""
import csv
import re
from pathlib import Path

from flask import Blueprint, jsonify

bp = Blueprint("results", __name__, url_prefix="/api")
RESULTS = Path(__file__).resolve().parents[2] / "results"
SAFE = re.compile(r"^[A-Za-z0-9_\-]+$")


def _num(v):
    for cast in (int, float):
        try:
            return cast(v)
        except ValueError:
            pass
    return {"True": True, "False": False}.get(v, v)


@bp.get("/results")
def list_results():
    return jsonify({sub: sorted(p.stem for p in (RESULTS / sub).glob("*.csv")) for sub in ("summary", "raw")})


@bp.get("/results/<name>")
def get_result(name):
    if not SAFE.match(name):
        return jsonify(error="bad name"), 400
    for sub in ("summary", "raw"):
        path = RESULTS / sub / f"{name}.csv"
        if path.exists():
            with open(path, newline="") as f:
                return jsonify([{k: _num(v) for k, v in r.items()} for r in csv.DictReader(f)])
    return jsonify(error="not found"), 404
