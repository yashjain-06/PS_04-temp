"""Baseline vs ACO route comparison on a site (owner: M3)."""
from __future__ import annotations

import statistics as st

from src.logistics.astar import shortest_path
from src.logistics.router import Router
from src.utils.config import load_config


def sample_pairs(blueprint, grid, limit=12) -> list:
    """(depot, stand cell next to a target) pairs, spread over the build zone."""
    stands = sorted({n for t in blueprint.targets for n in grid.neighbors4(t) if n not in blueprint.targets})
    step = max(1, len(stands) // max(1, limit // len(blueprint.depots)))
    picked = stands[::step]
    return [(d, s) for d in blueprint.depots for s in picked][: limit * 2]


def compare_routes(blueprint, grid, seed=0, aco_cfg=None, limit=12) -> dict:
    aco_cfg = aco_cfg if aco_cfg is not None else load_config()["aco"]      # the tuned configs/aco.yaml
    base = Router(grid, use_aco=False, seed=seed)
    aco = Router(grid, use_aco=True, seed=seed, aco_cfg=aco_cfg)
    rows = []
    for src, dst in sample_pairs(blueprint, grid, limit):
        opt = shortest_path(base.graph, src, dst)
        if not opt:
            continue
        b, a = base.get_route(src, dst), aco.get_route(src, dst)
        rows.append({"src": src, "dst": dst, "optimal": len(opt), "baseline": len(b), "aco": len(a),
                     "baseline_hits_obstacle": any(c in grid.obstacles for c in b),
                     "aco_hits_obstacle": any(c in grid.obstacles for c in a), "baseline_route": b, "aco_route": a,
                     "aco_history": aco.aco.history.get((src, dst), [])})
    n = len(rows)
    curves = [(r["aco_history"], r["optimal"]) for r in rows
              if r["aco_history"] and all(v is not None for v in r["aco_history"])]
    width = max((len(h) for h, _ in curves), default=0)               # runs may stop early: pad with the final value
    conv = [round(st.fmean((h + [h[-1]] * (width - len(h)))[i] / opt for h, opt in curves), 3) for i in range(width)]
    return {"pairs": n,
            "mean_optimal": round(st.fmean(r["optimal"] for r in rows), 2) if n else None,
            "mean_baseline": round(st.fmean(r["baseline"] for r in rows), 2) if n else None,
            "mean_aco": round(st.fmean(r["aco"] for r in rows), 2) if n else None,
            "baseline_obstacle_rate": round(sum(r["baseline_hits_obstacle"] for r in rows) / n, 3) if n else None,
            "aco_obstacle_rate": round(sum(r["aco_hits_obstacle"] for r in rows) / n, 3) if n else None,
            "aco_vs_optimal": round(st.fmean(r["aco"] / r["optimal"] for r in rows), 3) if n else None,
            "aco_fallbacks": aco.aco.fallbacks, "convergence": conv, "rows": rows}
