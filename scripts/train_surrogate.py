"""Train the build-time surrogate and print its held-out accuracy (owner: M4).

  python scripts/make_surrogate_data.py && python scripts/train_surrogate.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ml.surrogate import recommend, train  # noqa: E402

if __name__ == "__main__":
    report = train(ROOT / "results" / "raw" / "surrogate_data.csv")
    print(json.dumps(report, indent=1))
    for bp in ("wall_with_opening", "u_shape"):
        for aco in (False, True):
            r = recommend(f"blueprints/{bp}.json", aco)
            print(f"{bp:18} aco={aco!s:5} -> best agents {r['best_n_agents']:2}, predicted {r['predicted_build_time']} ticks")
