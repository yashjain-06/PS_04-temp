"""Check the code against docs/interfaces.md.   (owner: M4)

  python scripts/check_interfaces.py          # model chosen by src/sim/factory.py
  python scripts/check_interfaces.py --real   # force M1's real model
Exit code 1 if any hard check fails.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.interface_check import check_model, check_modules  # noqa: E402
from src.utils.config import load_config  # noqa: E402

SOFT = {"one robot per cell"}      # reported, not fatal, because FakeModel has no collisions


def show(title, results):
    print(f"\n{title}")
    bad = 0
    for name, ok, detail in results:
        tag = "PASS" if ok else ("WARN" if name in SOFT else "FAIL")
        bad += tag == "FAIL"
        print(f"  [{tag}] {name}" + (f"  - {detail}" if detail and not ok else ""))
    return bad


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", action="store_true")
    a = ap.parse_args()
    cfg = load_config()
    params = {"blueprint": cfg["simulation"]["blueprint"], "n_agents": 10, "fail_rate": 0.0, "use_aco": False,
              "seed": 42, "fail_at_tick": 200, "max_ticks": cfg["simulation"]["max_ticks"]}
    bad = show("Module API (M1/M2/M3 functions)", check_modules())
    try:
        if a.real:
            from src.sim.model import build_model
            model = build_model(**params)
        else:
            from src.sim.factory import make_model
            model = make_model(params)
        bad += show("Model contract", check_model(model, params["max_ticks"]))
    except Exception as e:      # noqa: BLE001
        print(f"\n[FAIL] could not build the model: {e!r}")
        bad += 1
    print(f"\n{bad} hard failure(s)")
    sys.exit(1 if bad else 0)
