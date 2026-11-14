import csv, tempfile
from pathlib import Path
from src.experiments.analysis import mean_std_ci, read_rows, summarize, write_summary
from src.experiments.runner import expand_config, run_grid, run_one
from src.utils.config import load_yaml

BP = "blueprints/wall_with_opening.json"
BASE = {"blueprint": BP, "n_agents": 10, "fail_rate": 0.0, "use_aco": False,
        "seed": 1, "fail_at_tick": 30, "max_ticks": 3000}


def test_expand_scaling_and_failures():
    assert len(expand_config(load_yaml("configs/scaling.yaml"))) == 4 * 5 * 2
    runs = expand_config(load_yaml("configs/failures.yaml"))
    assert len(runs) == 3 * 5 and {r["fail_rate"] for r in runs} == {0.0, 0.1, 0.3}


def test_same_seed_reproducible():
    a, b = run_one(BASE), run_one(dict(BASE))
    assert a.to_row() == b.to_row()


def test_different_seeds_run_and_complete():
    for s in (1, 2, 3):
        r = run_one({**BASE, "seed": s})
        assert r.completed and r.exact and r.accuracy == 1.0 and r.efficiency > 0


def test_csv_roundtrip_and_summary_slowdown():
    runs = [{**BASE, "n_agents": 20, "fail_rate": fr, "seed": s} for fr in (0.0, 0.3) for s in (1, 2, 3)]
    d = Path(tempfile.mkdtemp())
    rows = run_grid(runs, d / "raw.csv")
    back = read_rows(d / "raw.csv")
    assert len(back) == 6 and back[0]["completed"] is True and isinstance(back[0]["build_time"], int)
    summ = write_summary(back, d / "sum.csv")
    by = {r["fail_rate"]: r for r in summ}
    assert by[0.0]["slowdown"] == 1.0 and by[0.3]["slowdown"] >= 1.0
    assert by[0.0]["n_runs"] == 3 and (d / "sum.csv").exists()


def test_mean_std_ci():
    m, s, ci = mean_std_ci([10, 12, 14])
    assert m == 12 and abs(s - 2) < 1e-9 and abs(ci - 4.303 * 2 / 3 ** 0.5) < 1e-9
    assert mean_std_ci([5]) == (5, 0.0, 0.0)
