# Logistics (src/logistics)
One interface: `get_route(src, dst, blocked=())`. `blocked` = cells the robot has seen built.
- **Baseline:** straight staircase line (or biased random walk). Ignores rocks and blocks; robots detour locally.
- **ACO:** ants walk the site graph with probability ~ pheromone^alpha * (1/(1+distance to goal))^beta, a 6-cell tabu list,
  10% random exploration and loop erasure. Pheromone evaporates (rho 0.3); successful ants deposit q/length.
  Tuned values are in `configs/aco.yaml`. Measured on the barrier site: about 1.07x the optimal (A*) length, no A* fallbacks.
- The static ACO route per (start, goal) is cached and reused while it avoids blocks the robot knows about.
- `/logistics` shows both routes side by side with convergence; `/experiments` shows the effect on build time.

## PSO depot placement (src/logistics/pso.py)
Particles are vectors of depot coordinates snapped to free cells; fitness = mean walking distance (BFS) from the nearest depot to every cell
next to the build zone. 12 particles x 20 iterations (252 evaluations), compared with random search at the same budget.
The model accepts `depots=[[x, y], ...]` to use the result, and the live page has a checkbox for it.
