"""Particle Swarm Optimisation of depot positions (owner: M3).

Each particle is a vector of (x, y) for k depots. Fitness = mean over sampled 'stand cells' (free cells
next to a target) of the walking distance from the nearest depot, so a good layout puts depots close to the
build zone and on the right side of any barrier. Positions are snapped to valid free cells.
Compared against random search with the same number of fitness evaluations.
"""
from __future__ import annotations

from collections import deque

import numpy as np

from src.sim.seeding import make_rng


def _bfs(grid, start) -> dict:
    dist, q = {start: 0}, deque([start])
    while q:
        cur = q.popleft()
        for n in grid.neighbors4(cur):
            if n not in dist:
                dist[n] = dist[cur] + 1
                q.append(n)
    return dist


class DepotProblem:
    def __init__(self, blueprint, grid):
        self.grid, self.bp = grid, blueprint
        targets = blueprint.targets
        self.free = [c for c in grid.cells() if c not in targets]
        self.stands = sorted({n for t in targets for n in grid.neighbors4(t) if n not in targets})
        self._dist: dict = {}
        self.evals = 0

    def dist_from(self, cell) -> dict:
        if cell not in self._dist:
            self._dist[cell] = _bfs(self.grid, cell)
        return self._dist[cell]

    def snap(self, x: float, y: float):
        return min(self.free, key=lambda c: (c[0] - x) ** 2 + (c[1] - y) ** 2)

    def fitness(self, depots) -> float:
        self.evals += 1
        maps = [self.dist_from(d) for d in depots]
        total = 0.0
        for s in self.stands:
            total += min(m.get(s, 1e4) for m in maps)
        return total / len(self.stands)


def optimize_depots(blueprint, grid, n_depots=2, seed=0, particles=12, iters=20, w=0.6, c1=1.5, c2=1.5) -> dict:
    prob = DepotProblem(blueprint, grid)
    rng = make_rng(seed, "pso")
    lo, hi = np.array([0, 0] * n_depots, float), np.array([grid.width - 1, grid.height - 1] * n_depots, float)
    pos = rng.uniform(lo, hi, size=(particles, 2 * n_depots))
    vel = rng.uniform(-1, 1, size=pos.shape)

    def decode(v):
        cells = [prob.snap(v[2 * i], v[2 * i + 1]) for i in range(n_depots)]
        return tuple(dict.fromkeys(cells))                       # drop duplicates

    pbest, pbest_f = pos.copy(), np.array([prob.fitness(decode(p)) for p in pos])
    g = int(pbest_f.argmin())
    gbest, gbest_f, history = pbest[g].copy(), float(pbest_f[g]), [float(pbest_f[g])]
    for _ in range(iters):
        r1, r2 = rng.random(pos.shape), rng.random(pos.shape)
        vel = w * vel + c1 * r1 * (pbest - pos) + c2 * r2 * (gbest - pos)
        pos = np.clip(pos + vel, lo, hi)
        for i, p in enumerate(pos):
            f = prob.fitness(decode(p))
            if f < pbest_f[i]:
                pbest[i], pbest_f[i] = p.copy(), f
                if f < gbest_f:
                    gbest, gbest_f = p.copy(), f
        history.append(gbest_f)
    budget = prob.evals
    rs_rng, best_rs = make_rng(seed, "random_search"), 1e9                 # same number of evaluations
    for _ in range(budget):
        cand = tuple(prob.free[int(rs_rng.integers(len(prob.free)))] for _ in range(n_depots))
        best_rs = min(best_rs, prob.fitness(cand))
    original = prob.fitness(tuple(blueprint.depots))
    return {"depots": [list(d) for d in decode(gbest)], "fitness": round(gbest_f, 3), "original_depots": [list(d) for d in blueprint.depots],
            "original_fitness": round(original, 3), "random_search_fitness": round(best_rs, 3),
            "evaluations": budget, "history": [round(h, 3) for h in history]}
