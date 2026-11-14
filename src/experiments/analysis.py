"""Average over seeds, 95% CIs and slowdown (owner: M4). Stdlib only, so it runs anywhere."""
from __future__ import annotations

import csv
import math
import statistics as st
from pathlib import Path

GROUP = ("blueprint", "n_agents", "fail_rate", "use_aco")
# two-sided 95% t critical values by degrees of freedom; >10 uses ~2.0 (approximation)
T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228}


def _convert(k, v):
    if v in ("True", "False"):
        return v == "True"
    if v in ("", "None"):
        return None
    if k in ("blueprint",):
        return v
    for cast in (int, float):
        try:
            return cast(v)
        except ValueError:
            pass
    return v


def read_rows(path: str | Path) -> list[dict]:
    """Read a raw or summary CSV, converting numbers and booleans."""
    with open(path, newline="") as f:
        return [{k: _convert(k, v) for k, v in r.items()} for r in csv.DictReader(f)]


def mean_std_ci(values: list[float]) -> tuple[float, float, float]:
    n = len(values)
    m = st.fmean(values)
    if n < 2:
        return m, 0.0, 0.0
    s = st.stdev(values)
    return m, s, T95.get(n - 1, 2.0) * s / math.sqrt(n)


def summarize(rows: list[dict], keys: tuple = GROUP) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        groups.setdefault(tuple(r[k] for k in keys), []).append(r)
    out = []
    for g, rs in sorted(groups.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
        row = dict(zip(keys, g))
        row["n_runs"] = len(rs)
        row["completed_rate"] = round(sum(r["completed"] for r in rs) / len(rs), 3)
        row["exact_rate"] = round(sum(r["exact"] for r in rs) / len(rs), 3)
        for metric in ("build_time", "accuracy", "efficiency", "blocked_ticks"):
            m, s, ci = mean_std_ci([r[metric] for r in rs])
            row[f"{metric}_mean"], row[f"{metric}_std"], row[f"{metric}_ci95"] = round(m, 4), round(s, 4), round(ci, 4)
        out.append(row)
    return add_slowdown(out)


def add_slowdown(summary: list[dict]) -> list[dict]:
    """slowdown = mean build time with failures / mean build time at 0% failure (same blueprint, agents, ACO)."""
    base = {(r["blueprint"], r["n_agents"], r["use_aco"]): r["build_time_mean"]
            for r in summary if r["fail_rate"] == 0.0}
    for r in summary:
        b = base.get((r["blueprint"], r["n_agents"], r["use_aco"]))
        r["slowdown"] = round(r["build_time_mean"] / b, 3) if b else None
    return summary


def write_summary(rows: list[dict], path: str | Path) -> list[dict]:
    summ = summarize(rows)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summ[0].keys()))
        w.writeheader()
        w.writerows(summ)
    return summ
