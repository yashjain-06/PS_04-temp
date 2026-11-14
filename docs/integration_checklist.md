# Hour-14 integration checklist (M4 runs this, owner: M4)

Run in order. Stop at the first failure and message the owner named on that line.

## Before the call
- [ ] Everyone pulled `main`; `pip install -r requirements.txt` done; `pytest -q` passes on your own laptop.
- [ ] `python scripts/check_interfaces.py --real` has been shared in chat so owners see their own gaps.

## 1. Module API (M1, M2, M3)
- [ ] `python scripts/check_interfaces.py --real`: "Module API" section shows no FAIL.
  - `env/rules.py` missing -> M1. `agents/*` missing -> M2. `logistics/router.py` missing -> M3.

## 2. Model contract (M1)
- [ ] "Model contract" section: all PASS. `one robot per cell` must now be PASS (WARN means M2's collision handling is not in).
- [ ] `build completes` and `structure == blueprint (exact)` PASS on `wall_with_opening.json`.

## 3. Switch to the real model (M4)
- [ ] Set `USE_REAL_MODEL = True` in `src/sim/factory.py`.
- [ ] `pytest -q tests/test_e2e.py tests/test_failure.py tests/test_experiments.py` passes.
  - A failure here that FakeModel did not show is a real bug: note the seed and params and send to the owner.

## 4. Browser check (M4)
- [ ] `python scripts/run_server.py`, press Start with 10 agents: robots move, blocks appear, accuracy reaches 100%.
- [ ] Failure rate 30%: failed robots show a red X, the build still completes.
- [ ] Reload the page mid-run: state recovers from the stream.

## 5. Retune after integration (M4)
- [ ] Set `fail_at_tick` in `configs/failures.yaml` to about half the 0%-failure build time.
- [ ] Run `python scripts/run_all_experiments.py --quick`, open `/experiments`, and check the curves look plausible:
  build time should fall then flatten (congestion) as agents grow; ACO should not be slower than baseline.

## Decentralisation review (everyone, 10 minutes)
- [ ] No code outside `agents/` decides which robot builds which cell.
- [ ] Each robot reads only the blueprint and its radius-r observation (`tests/test_sensing.py`).
- [ ] FakeModel is not imported by anything the demo uses.
