# Frozen interfaces (hour 0-2)

Change anything here only with all four members agreeing in chat. Version: v1.

## Conventions
- A **Cell** is `(x, y)` or `(x, y, z)`. Flat 2D uses `z = 0`. In JSON, cells are `[x, y, z]` lists.
- Grid is `width x height` (x to the right, y down).
- All randomness comes from `src/sim/seeding.py` (`set_seed`, `make_rng(seed, stream)`).
- All parameters come from `configs/*.yaml` via `src/utils/config.py::load_config`.

## Python signatures
| Area | Owner | File | Signature |
|---|---|---|---|
| Placement rule | M1 | `src/env/rules.py` | `can_place(x, y, z=0) -> bool` |
| Support / order | M1 | `src/env/rules.py` | `is_supported(x,y,z)`, `order_ok(x,y,z)`, `is_occupied(x,y,z)` |
| Accuracy | M1 | `src/env/verify.py` | `accuracy(model) -> float` |
| Sensing | M2 | `src/agents/sensing.py` | `observe(agent, radius) -> Observation` (radius-r only) |
| Pheromone | M2 | `src/agents/stigmergy.py` | `deposit(x,y,amount)`, `read(x,y)`, `evaporate()` |
| Routing | M3 | `src/logistics/router.py` | `get_route(src, dst) -> list[Cell]` (baseline and ACO share this; toggled by `logistics.use_aco`) |
| Snapshot | M1 + M2 | `src/sim/snapshot.py` | `model.snapshot() -> dict` (JSON-safe, shape below) |
| Failure | M4 | `src/sim/failure.py` | `fail_agents(model, rate, tick)` sets `agent.failed = True` |
| Done check | M1 | `src/sim/model.py` | `model.build_complete() -> bool`, `model.tick -> int` |

## Agent state (serialisable, M2)
`id, x, y, state in {seek, carry, place, return}, carrying: bool, failed: bool`
A failed agent stops moving and remains as a static obstacle.

## Snapshot JSON
See `web/static/fake_snapshot.json` for a full sample.
```json
{
  "tick": 42,
  "grid": {"width": 20, "height": 10, "depth": 1},
  "blueprint": [[4,5,0],[5,5,0]],
  "structure": [[4,5,0]],
  "depots": [[0,2],[0,7]],
  "agents": [{"id":0,"x":3,"y":4,"state":"carry","carrying":true,"failed":false}],
  "pheromone": [[0.0, 0.2]],
  "metrics": {"accuracy": 0.35, "placed": 7, "active_agents": 9, "failed_agents": 1}
}
```
`pheromone` is a `height x width` matrix of floats in [0, 1].

## HTTP API (M4)
| Endpoint | Body / Returns |
|---|---|
| `POST /api/start` | `{blueprint, n_agents, fail_rate, use_aco, seed}` -> `{run_id}` |
| `POST /api/step` | `{n}` -> latest snapshot after n ticks |
| `GET /api/state` | latest snapshot |
| `GET /api/stream` | Server-Sent Events, one snapshot per message |
| `POST /api/pause`, `POST /api/reset` | `{ok: true}` |
| `GET /api/metrics` | `{build_time, accuracy, efficiency, slowdown}` |
| `GET /api/results/<name>` | CSV from `results/` as JSON rows |

## Metrics (`src/experiments/metrics.py`)
- **build_time**: ticks until the structure is complete (`max_ticks` if never)
- **accuracy**: matching cells / blueprint cells
- **exact**: structure equals blueprint (no missing and no extra cells)
- **efficiency**: blocks placed / agent-ticks
- **slowdown**: build time with failures / build time without failures

## Blueprint JSON (M1)
`{name, width, height, depth, depots: [[x,y]], cells: [[x,y,z]]}`

## Decentralisation rule
A robot may use only: the blueprint, its own state, and a radius-r observation (cells, robots, pheromone).
No central task scheduler. Document the final answer in `docs/decentralisation.md`.

## v1.2 (current, implemented)
- `get_route(src, dst, blocked=())` gained an optional `blocked` set. Baseline ignores it; ACO plans around it.
- Snapshot gained `obstacles` (list of [x, y]) and `traffic` (height x width floats in [0, 1]); `metrics` gained `blocked_ticks`.
- The model is `src/sim/model.py::build_model(**params)` (plain Python, no Mesa). `params`: `blueprint, n_agents, fail_rate, use_aco,
  seed, fail_at_tick, max_ticks`. It provides `step(), snapshot(), build_complete(), accuracy(), agent_ticks(), structure_cells(),
  blueprint_cells(), blocked_ticks, tick, max_ticks, blocks_placed, agents, events`.
- `src/sim/factory.py` uses the real model by default; `PS4_FAKE_MODEL=1` selects the UI-only FakeModel.
- `build_model(..., depots=[[x, y], ...])` overrides the blueprint's depots (used with PSO).
- HTTP additions: `GET /api/depots/optimize`, `POST /api/start` accepts `pso_depots`, `/api/blueprint` (GET/validate/save), `/api/insights`, `/api/predict`, `/api/logistics`.
- Blueprint paths are restricted to the `blueprints/` folder.
- Only flat blueprints (z = 0) are supported.
