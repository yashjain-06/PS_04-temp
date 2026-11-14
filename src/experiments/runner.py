"""Experiment runner: seeds x agents x failure x ACO -> CSV (owner: M4)."""
from __future__ import annotations

import csv
import itertools
from dataclasses import fields
from pathlib import Path

from src.experiments import metrics as M
from src.sim.factory import make_model
from src.utils.config import load_config, load_yaml

ROOT = Path(__file__).resolve().parents[2]
FIELDS = [f.name for f in fields(M.RunMetrics)]


def _as_list(v):
    return list(v) if isinstance(v, (list, tuple)) else [v]


def expand_config(cfg: dict) -> list[dict]:
    """Turn a scaling/failures YAML dict into one params dict per run."""
    d = load_config()
    blueprints = _as_list(cfg.get("blueprints") or d["simulation"]["blueprint"])
    n_list = _as_list(cfg.get("agent_counts") or cfg.get("n_agents") or d["simulation"]["n_agents"])
    f_list = _as_list(cfg.get("failure_rates") if cfg.get("failure_rates") is not None
                      else cfg.get("failure_rate", d["failure"]["rate"]))
    aco_list = _as_list(cfg.get("use_aco", d["logistics"]["use_aco"]))
    seeds = _as_list(cfg.get("seeds") or d["simulation"]["seed"])
    runs = []
    for bp, n, fr, aco, seed in itertools.product(blueprints, n_list, f_list, aco_list, seeds):
        runs.append({"blueprint": bp, "n_agents": int(n), "fail_rate": float(fr), "use_aco": bool(aco),
                     "seed": int(seed), "fail_at_tick": int(cfg.get("fail_at_tick", d["failure"]["at_tick"])),
                     "max_ticks": int(cfg.get("max_ticks", d["simulation"]["max_ticks"]))})
    return runs


def run_one(params: dict) -> M.RunMetrics:
    model = make_model(params)
    while not model.build_complete() and model.tick < params["max_ticks"]:
        model.step()
    done = model.build_complete()
    st, bp = model.structure_cells(), model.blueprint_cells()
    ticks = model.agent_ticks()
    return M.RunMetrics(
        seed=params["seed"], blueprint=Path(params["blueprint"]).stem, n_agents=params["n_agents"],
        fail_rate=params["fail_rate"], use_aco=params["use_aco"],
        build_time=M.build_time(model.tick if done else None, params["max_ticks"]),
        accuracy=round(M.accuracy(st, bp), 4), exact=M.is_exact(st, bp), extra_cells=M.extra_cells(st, bp),
        blocks_placed=model.blocks_placed, agent_ticks=ticks,
        efficiency=round(M.efficiency(model.blocks_placed, ticks), 5), completed=done,
        blocked_ticks=int(getattr(model, "blocked_ticks", 0)))


def run_grid(runs: list[dict], out_csv: str | Path, progress: bool = False) -> list[dict]:
    rows = []
    for i, p in enumerate(runs, 1):
        rows.append(run_one(p).to_row())
        if progress:
            print(f"\r{i}/{len(runs)}", end="", flush=True)
    if progress:
        print()
    out = Path(out_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    return rows


def run_config_file(path: str | Path, name: str, quick: bool = False, progress: bool = True):
    cfg = load_yaml(path)
    if quick:
        cfg["seeds"] = _as_list(cfg.get("seeds", [1]))[:2]
    runs = expand_config(cfg)
    return run_grid(runs, ROOT / "results" / "raw" / f"{name}.csv", progress)
