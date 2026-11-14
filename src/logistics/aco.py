"""Ant Colony Optimisation for transport routes (owner: M3).

Virtual ants walk the site graph from src to dst. Each ant picks the next cell with probability
proportional to tau^alpha * eta^beta (tau = pheromone, eta = 1/(1+distance-to-dst)). After each
iteration pheromone evaporates (rho) and ants that reached dst deposit q/length on their edges,
so shorter routes get reinforced. Pheromone tables are kept per destination, so later queries
to the same place start from what earlier ants learned.
"""
from __future__ import annotations

import random
import zlib

from src.logistics.astar import shortest_path


class AntColony:
    def __init__(self, graph, n_ants=8, n_iter=5, alpha=1.0, beta=3.0, rho=0.3, q=10.0, seed=0, early_stop=True, max_len_factor=3.0, epsilon=0.1, tabu=6):
        self.graph, self.n_ants, self.n_iter = graph, n_ants, n_iter
        self.alpha, self.beta, self.rho, self.q = alpha, beta, rho, q
        self.rng = random.Random(zlib.crc32(f"aco:{seed}".encode()))
        self.tau: dict = {}                    # dst -> {(u, v): pheromone}
        self.cache: dict = {}                  # (src, dst) -> route
        self.history: dict = {}                # (src, dst) -> best length after each iteration
        self.fallbacks = 0
        self.early_stop = early_stop
        self.max_len_factor, self.epsilon, self.tabu = max_len_factor, epsilon, tabu

    @staticmethod
    def _erase_loops(path):
        out, at = [], {}
        for c in path:
            if c in at:                                  # revisited a cell: cut the loop
                for gone in out[at[c] + 1:]:
                    del at[gone]
                out = out[: at[c] + 1]
            else:
                at[c] = len(out)
                out.append(c)
        return out

    def _walk(self, src, dst, tau, blocked=()):
        """One ant. A short tabu list (not a permanent visited set) lets it back out of dead ends;
        with probability `epsilon` it explores uniformly; loops are erased from the finished path."""
        path, recent, cur = [src], [src], src
        maxlen = self.max_len_factor * (abs(src[0] - dst[0]) + abs(src[1] - dst[1])) + 12
        while cur != dst:
            if len(path) > maxlen:
                return None
            nbrs = [n for n in self.graph.neighbors(cur) if n not in blocked]
            options = [n for n in nbrs if n not in recent] or nbrs
            if not options:
                return None
            if self.rng.random() < self.epsilon:
                nxt = options[int(self.rng.random() * len(options))]
            else:
                w = [(tau.get((cur, n), 1.0) ** self.alpha) * ((1.0 / (1 + abs(n[0] - dst[0]) + abs(n[1] - dst[1]))) ** self.beta)
                     for n in options]
                r, acc, nxt = self.rng.random() * sum(w), 0.0, options[-1]
                for n, wi in zip(options, w):
                    acc += wi
                    if r <= acc:
                        nxt = n
                        break
            path.append(nxt)
            recent.append(nxt)
            if len(recent) > self.tabu:
                recent.pop(0)
            cur = nxt
        return self._erase_loops(path)

    def route(self, src, dst, blocked=()) -> list:
        """Best route avoiding `blocked` cells (cells the caller knows are built).

        The obstacle-free route for (src, dst) is cached and reused as long as it does not touch a blocked
        cell; only when it does is a fresh (uncached) route planned around the blocked cells."""
        key = (src, dst)
        if src == dst or src not in self.graph or dst not in self.graph or dst in blocked:
            return []
        if key not in self.cache:
            self.cache[key] = self._search(src, dst, ())
        static = self.cache[key]
        if not blocked or not any(c in blocked for c in static):
            return list(static)
        return self._search(src, dst, blocked)

    def _search(self, src, dst, blocked) -> list:
        tau = self.tau.setdefault(dst, {})
        best, hist, stall = None, [], 0
        lower = abs(src[0] - dst[0]) + abs(src[1] - dst[1])          # no route can be shorter than this
        for it in range(self.n_iter):
            found = [p for p in (self._walk(src, dst, tau, blocked) for _ in range(self.n_ants)) if p]
            for e in tau:
                tau[e] *= (1 - self.rho)
            for p in found:
                for u, v in zip(p, p[1:]):
                    tau[(u, v)] = tau.get((u, v), 1.0) + self.q / len(p)
            if found:
                it_best = min(found, key=len)
                for u, v in zip(it_best, it_best[1:]):                   # elitist reinforcement
                    tau[(u, v)] = tau.get((u, v), 1.0) + self.q / len(it_best)
                if best is None or len(it_best) < len(best):
                    best, stall = it_best, 0
                else:
                    stall += 1
            hist.append(len(best) - 1 if best else None)
            if best and (len(best) - 1 == lower or (self.early_stop and it >= 3 and stall >= 3)):      # optimal for sure, or no recent improvement
                break
        if best is None:                                                  # no ant arrived: fall back
            self.fallbacks += 1
            return list(shortest_path(self.graph, src, dst, frozenset(blocked)) or [])
        if not blocked:
            self.history[(src, dst)] = hist
        return best[1:]
