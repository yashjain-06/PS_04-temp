"""Static PNG charts from the summary CSVs, for slides and the README (owner: M4)."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.experiments.analysis import read_rows  # noqa: E402


def plot_scaling(summary_csv, out_png) -> None:
    rows = read_rows(summary_csv)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    for aco, label in ((False, "Baseline routes"), (True, "ACO routes")):
        rs = sorted((r for r in rows if r["use_aco"] == aco and r["fail_rate"] == 0), key=lambda r: r["n_agents"])
        xs = [r["n_agents"] for r in rs]
        ax[0].errorbar(xs, [r["build_time_mean"] for r in rs], yerr=[r["build_time_ci95"] for r in rs], marker="o", capsize=3, label=label)
        ax[1].errorbar(xs, [r["efficiency_mean"] for r in rs], yerr=[r["efficiency_ci95"] for r in rs], marker="o", capsize=3, label=label)
    ax[0].set(xlabel="Agents", ylabel="Build time (ticks)", title="Build time vs agents (95% CI)")
    ax[1].set(xlabel="Agents", ylabel="Blocks per agent-tick", title="Efficiency vs agents")
    for a in ax:
        a.legend()
        a.grid(alpha=0.3)
    fig.tight_layout()
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=130)
    plt.close(fig)


def plot_failures(summary_csv, out_png) -> None:
    rows = sorted(read_rows(summary_csv), key=lambda r: r["fail_rate"])
    labels = [f"{round(r['fail_rate'] * 100)}%" for r in rows]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].bar(labels, [r["build_time_mean"] for r in rows], yerr=[r["build_time_ci95"] for r in rows], capsize=4)
    ax[0].set(xlabel="Robots failed", ylabel="Build time (ticks)", title="Build time under failures")
    ax[1].bar(labels, [r["slowdown"] for r in rows])
    ax[1].axhline(1.0, color="red", ls="--", lw=1)
    ax[1].set(xlabel="Robots failed", ylabel="Slowdown (x)", title="Slowdown (structure exact in "
              + f"{round(100 * min(r['exact_rate'] for r in rows))}% of runs)")
    for a in ax:
        a.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=130)
    plt.close(fig)
