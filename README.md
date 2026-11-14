# PS4: Swarm Intelligence for Autonomous Building Construction

A decentralised swarm of simple robots builds a structure from a blueprint using local rules and
stigmergy (pheromone). There is **no central scheduler**. Ant Colony Optimisation (ACO) plans material
logistics and is compared with a naive straight-line baseline. A Flask web app shows the build live.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q                                              # ~1-2 minutes
python scripts/run_server.py                           # http://127.0.0.1:5000
python scripts/run_all_experiments.py                  # scaling + failure studies -> results/
python scripts/make_gif.py                             # GIFs, charts, heatmaps -> results/
python scripts/check_interfaces.py                     # verifies code against docs/interfaces.md
python scripts/make_surrogate_data.py && python scripts/train_surrogate.py   # ML surrogate (data and model already included)
```
Web pages: `/` live simulation, `/editor` blueprint drawing grid, `/logistics` baseline vs ACO (and PSO depots), `/experiments` charts,
`/insights` ML predictions, `/about`. `make test`, `make run`, `make experiments`, `make media`, `make surrogate` are shortcuts.

## Putting it on the web
See `docs/deployment.md` (same Wi-Fi, ngrok link, Render, Docker). One worker process, threads for concurrency; each visitor gets their own simulation.

## What is implemented
| Area | Where |
|---|---|
| Blueprint loader (JSON / ASCII), rules compiler, support + reachability ordering rules, buildability check | `src/env/` |
| Robots: FSM (seek, carry, place, return), radius-2 sensing, pheromone, right-of-way, random back-off, wall-following | `src/agents/` |
| Logistics: path graph, A*, baseline (straight / random), ACO, one `get_route` interface, comparison tool | `src/logistics/` |
| Plain-Python swarm model, snapshot, failure injection, event log, seeding | `src/sim/` |
| Metrics, multi-seed runner, 95% CI analysis, slowdown | `src/experiments/` |
| Web app, API, canvas charts, logistics page | `web/` |
| GIF export, PNG charts, heatmaps | `src/viz/`, `scripts/make_gif.py` |
| PSO depot placement | `src/logistics/pso.py` |
| ML surrogate: predicts build time, suggests a swarm size | `src/ml/`, `scripts/train_surrogate.py` |
| Blueprint editor (draw, validate, save, simulate) | `web/templates/blueprint_editor.html`, `web/api/blueprint_routes.py` |

Four blueprints in `blueprints/` (simple wall, wall with an opening, 2-row wall, U shape). The site has a
barrier with a 2-cell gap between the depots and the build zone, which is what makes logistics matter.

## What each robot knows (transparency)
Static knowledge: the blueprint (target cells), the site map (grid, rocks, depots). Local sensing: a
radius-2 window of built cells, other robots and pheromone. Memory: the blocks it has itself seen.
It is never told what to build or where to go. Details and honest caveats: `docs/decentralisation.md`.

## Results (from `scripts/run_all_experiments.py`, 5 seeds, `results/summary/`)
- ACO builds the wall about 2.4x faster than the baseline at 10 agents (67 vs 163 ticks).
- Congestion at the depots sets in as agents are added; at 50 agents the ACO advantage is gone.
- With 30% of 30 robots failing mid-build, every structure is still exact; slowdown is about 1.3x.

- **PSO depot placement** (`/api/depots/optimize`, the "PSO depot placement" checkbox): moves the depots next to the build zone.
  Distance fitness 2.5 vs 21.5 for the original layout, better than random search with the same budget. In simulation the baseline at
  10 agents drops from 163 to 29 ticks and ACO from 67 to 34, structures still exact. One case got worse: `u_shape` with ACO at 30 agents (156 vs 141).
- **ML surrogate** (offline analysis, never controls robots): on a held-out seed R2 = 0.94, MAE = 25 ticks (guessing the mean gives 98).
  It does NOT generalise to an unseen blueprint (leave-one-blueprint-out R2 from -0.19 to 0.68) because it saw only 3 blueprints.

## Limits and honesty
See `docs/limitations.md` (flat 2D only, no sensor noise / battery / physics, a fault model that stops dead
robots from sealing the site, FakeModel is UI-only).

## Team
| Member | Area |
|---|---|
| M1 | `src/env/`, `src/sim/model.py`, `src/sim/snapshot.py`, blueprints |
| M2 | `src/agents/` |
| M3 | `src/logistics/` |
| M4 (lead) | `src/experiments/`, `src/sim/failure.py`, `web/`, `src/viz/`, integration |
