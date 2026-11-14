# What each robot knows, and what is shared

## A robot HAS
- **Blueprint** (static): the set of target cells.
- **Site map** (static): grid size, rocks, depot positions.
- **Own state**: position, FSM state, carrying flag, a committed goal, a route, and a **memory of blocks it has itself seen**.
- **Local observation** (`src/agents/sensing.py::observe`): everything inside a Chebyshev radius of 2:
  built cells, unbuilt targets, other robots, rocks, pheromone. `tests/test_sensing.py` checks nothing outside the radius leaks in.

## A robot does NOT have
- Any task list, queue or assignment. Nothing tells a robot which cell to build.
- Other robots' goals or states, or the global structure outside its window.

## What the environment (the model) does
It only enforces physics: one robot per cell, a placement is accepted only if the rules allow it, and it records metrics.
Each tick every robot runs its own FSM in a seeded random order (asynchronous updates).

## Coordination
- **Stigmergy:** the built structure itself, plus pheromone left by robots that place a block (fades 5% per tick).
  Loaded robots with no legal site in view follow pheromone toward recent building.
- **Right of way:** carrying beats empty, then lower id. The loser side-steps after one blocked tick; the winner waits 4 ticks and then backs off.
- **Obstacles:** contour (wall) following with a "leave when closer than the hit point" rule; random back-off against deadlock.

## Caveats stated honestly
1. **Placement legality is evaluated by the environment's rule engine** (`src/env/rules.py`). The ordering rule ("do not seal off
   an unbuilt cell") is computed with a breadth-first search over the whole structure and cached per structure version. Robots only
   query it for cells inside their sensing window, so they read one bit per sensed cell, like TERMES' precompiled rules,
   but the bit is derived from global structure state. It selects *which cells are legal*, never *who builds what*.
2. Robots know the static site map (rocks, depots). The baseline router ignores it on purpose; the ACO router uses it.
3. The ACO router plans on the static graph plus the blocks that robot has seen. There is no shared route table between robots.
