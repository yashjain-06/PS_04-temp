"""Run an experiment config and write raw + summary CSVs (owner: M4).

  python scripts/run_all_experiments.py                 # scaling + failures
  python scripts/run_all_experiments.py --quick         # 2 seeds each, for a fast check
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.experiments.analysis import read_rows, write_summary  # noqa: E402
from src.experiments.runner import run_config_file  # noqa: E402

STUDIES = {"scaling": "configs/scaling.yaml", "failures": "configs/failures.yaml"}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=list(STUDIES))
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    for name, cfg in STUDIES.items():
        if a.only and a.only != name:
            continue
        print(f"== {name} ==")
        run_config_file(ROOT / cfg, name, quick=a.quick)
        summ = write_summary(read_rows(ROOT / "results" / "raw" / f"{name}.csv"),
                             ROOT / "results" / "summary" / f"{name}_summary.csv")
        for r in summ:
            print(f"n={r['n_agents']:>2} fail={r['fail_rate']:.1f} aco={str(r['use_aco']):5} "
                  f"time={r['build_time_mean']:>7.1f} ±{r['build_time_ci95']:<6.1f} "
                  f"acc={r['accuracy_mean']:.2f} exact={r['exact_rate']:.2f} slowdown={r['slowdown']}")
