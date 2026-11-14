# What the simulation leaves out

- **Flat 2D only.** No 3D voxels, climbing or physics. Robots cannot walk on blocks. (`depth` > 1 is rejected.)
- **No sensor noise, battery, wheel slip, communication delay or hardware faults** other than the injected stop failures.
- **Discrete time:** one cell per tick, robots update one after another in a seeded random order.
- **Unlimited block supply** at depots; a depot cell holds one robot, so depots are where congestion appears.
- **Fault model:** a failed robot stops and stays as a static obstacle. If its position would make the site physically
  unbuildable (it sits on a build cell or depot, or would seal off unbuilt targets), it first coasts to the nearest harmless cell.
  Without this, two dead robots in the 2-cell bridge can end the job for any swarm. This makes failures slightly optimistic.
- **ACO** runs once per (start, goal) and is reused; it is a route planner, not a live learning loop across robots.
- **Blueprints with enclosed corridors** (e.g. a 3-row wall built from the middle) can deadlock robots that cannot climb.
  `RuleSet.check_buildable` finds dead ends in the *rules*, not traffic jams.
- **FakeModel** (`src/sim/fake_model.py`) is a UI stand-in with a central target list. Never demo it.
- Numbers come from 5 seeds per setting on a 24x12 site; they show trends, not general constants.
- **ML:** only a build-time surrogate (gradient boosting) is implemented. It was trained on 144 runs of 3 blueprints and is only reliable on those;
  see the leave-one-blueprint-out rows. **Not implemented:** the RL policy with action masking, Optuna tuning of ACO (the parameters were tuned by hand),
  and image-to-blueprint.
- **PSO depots** change the site design (depots sit beside the build zone). That is a legitimate use of PSO for layout tuning, but it also removes
  most of the transport problem, so compare ACO and baseline on the original layout.
