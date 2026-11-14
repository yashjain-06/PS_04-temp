"""Fault injection: disable a share of robots mid-build (owner: M4).

Contract (docs/interfaces.md): a failed agent stops acting and stays in its cell as a
static obstacle. Works with dict agents (FakeModel) and objects with a `.failed` attribute
(M2's Builder). The model must expose `model.agents` (list) and may expose `model.events`.
"""
from __future__ import annotations

from src.sim.seeding import make_rng


def _get(a, key):
    return a[key] if isinstance(a, dict) else getattr(a, key)


def _set(a, key, value):
    if isinstance(a, dict):
        a[key] = value
    else:
        setattr(a, key, value)


def _agents(model):
    agents = getattr(model, "agents", None)
    if agents is None:
        agents = model.schedule.agents          # Mesa 2.x fallback
    return list(agents)


def fail_agents(model, rate: float, tick: int = 0, seed: int = 0) -> list[int]:
    """Disable round(rate * N) currently-active agents. Returns the ids that failed.

    Deterministic for a given (seed, tick), independent of other random streams.
    """
    if not 0.0 <= rate <= 1.0:
        raise ValueError("rate must be between 0 and 1")
    agents = _agents(model)
    active = [a for a in agents if not _get(a, "failed")]
    k = min(len(active), int(rate * len(agents) + 0.5))
    if k == 0:
        return []
    rng = make_rng(seed, f"failure:{tick}")
    chosen = [active[int(i)] for i in rng.choice(len(active), size=k, replace=False)]
    ids = []
    for a in chosen:
        _set(a, "failed", True)
        ids.append(int(_get(a, "id")))
    log = getattr(model, "events", None)
    if log is not None:
        for i in sorted(ids):
            log.record(tick, "failed", agent=i)
    return sorted(ids)
