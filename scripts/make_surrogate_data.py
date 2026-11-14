"""Generate the surrogate's training data from real simulation runs (owner: M4).

  python scripts/make_surrogate_data.py          # ~2-3 minutes -> results/raw/surrogate_data.csv
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.experiments.runner import expand_config, run_grid  # noqa: E402

CFG = {"blueprints": ["blueprints/simple_wall.json", "blueprints/wall_with_opening.json", "blueprints/u_shape.json"],
       "agent_counts": [5, 10, 20, 30, 40, 50], "seeds": [1, 2, 3, 4], "failure_rate": 0.0, "use_aco": [False, True]}

if __name__ == "__main__":
    runs = expand_config(CFG)
    print(len(runs), "runs")
    run_grid(runs, ROOT / "results" / "raw" / "surrogate_data.csv", progress=True)
