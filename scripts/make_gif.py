"""Record demo media (owner: M4).

  python scripts/make_gif.py            # GIFs, charts and heatmaps into results/
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.sim.factory import make_model  # noqa: E402
from src.viz.heatmap import save_heatmaps  # noqa: E402
from src.viz.plots import plot_failures, plot_scaling  # noqa: E402
from src.viz.render_video import record_gif  # noqa: E402

P = {"blueprint": "blueprints/wall_with_opening.json", "n_agents": 20, "fail_rate": 0.0, "use_aco": True,
     "seed": 1, "fail_at_tick": 40, "max_ticks": 3000}

if __name__ == "__main__":
    out = ROOT / "results"
    print("ACO build:", record_gif(P, out / "media/build_aco.gif", every=2), "frames")
    print("baseline :", record_gif({**P, "use_aco": False}, out / "media/build_baseline.gif", every=3), "frames")
    print("failures :", record_gif({**P, "fail_rate": 0.3, "n_agents": 30}, out / "media/build_with_failures.gif", every=2), "frames")
    m = make_model({**P, "use_aco": False})
    while not m.build_complete():
        m.step()
    save_heatmaps(m.snapshot(), out / "heatmaps/traffic_baseline.png")
    for name, fn in (("scaling", plot_scaling), ("failures", plot_failures)):
        csv = out / "summary" / f"{name}_summary.csv"
        if csv.exists():
            fn(csv, out / "figures" / f"{name}.png")
            print("chart:", name)
