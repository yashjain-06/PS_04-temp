"""Turn experiment rows into model features (owner: M4)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np

from src.env.blueprint import load_blueprint
from src.env.grid import Grid
from src.experiments.analysis import read_rows
from src.logistics.pso import DepotProblem

ROOT = Path(__file__).resolve().parents[2]
FEATURES = ["n_agents", "inv_agents", "log_agents", "use_aco", "aco_x_inv", "aco_x_n", "n_cells", "stand_dist", "cells_x_inv"]


@lru_cache(maxsize=None)
def blueprint_features(blueprint: str) -> tuple:
    """(number of blocks, mean walking distance from the depots to the cells next to the build zone)."""
    path = blueprint if Path(blueprint).suffix else f"blueprints/{blueprint}.json"
    if not (ROOT / path).exists():
        path = f"blueprints/{Path(blueprint).stem}.json"
    bp = load_blueprint(path)
    prob = DepotProblem(bp, Grid(bp.width, bp.height, bp.obstacles, bp.depots))
    return float(len(bp.cells)), float(prob.fitness(tuple(bp.depots)))


def featurize(n_agents: float, use_aco: bool, blueprint: str) -> list:
    cells, dist = blueprint_features(blueprint)
    inv, aco = 1.0 / n_agents, float(bool(use_aco))
    return [n_agents, inv, float(np.log(n_agents)), aco, aco * inv, aco * n_agents, cells, dist, cells * inv]


def load_dataset(csv_path) -> tuple:
    """Returns X, y (build time), groups (blueprint names), seeds."""
    rows = [r for r in read_rows(csv_path) if r["fail_rate"] == 0 and r["completed"]]
    X = np.array([featurize(r["n_agents"], r["use_aco"], r["blueprint"]) for r in rows])
    y = np.array([r["build_time"] for r in rows], dtype=float)
    return X, y, np.array([r["blueprint"] for r in rows]), np.array([r["seed"] for r in rows])
