"""model -> JSON-safe dict for the browser (owner: M1 + M2). Shape: docs/interfaces.md."""
from __future__ import annotations


def snapshot(m) -> dict:
    failed = sum(a.failed for a in m.agents)
    return {
        "tick": int(m.tick),
        "grid": {"width": m.grid.width, "height": m.grid.height, "depth": 1},
        "blueprint": [[x, y, 0] for x, y in sorted(m.rules.targets, key=lambda c: (c[1], c[0]))],
        "structure": m.rules.structure.as_list(),
        "depots": [list(d) for d in m.depots.positions],
        "obstacles": [list(o) for o in sorted(m.grid.obstacles)],
        "agents": [a.state_dict() for a in m.agents],
        "pheromone": m.pheromone.as_list(),
        "traffic": m.congestion.heat(),
        "metrics": {"accuracy": round(m.accuracy(), 3), "placed": int(m.blocks_placed),
                    "active_agents": len(m.agents) - failed, "failed_agents": failed,
                    "complete": m.build_complete(), "blocked_ticks": int(m.congestion.blocked_ticks)},
    }
