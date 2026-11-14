"""Serialisable robot state for the browser (owner: M2)."""


def agent_state(a) -> dict:
    return {"id": int(a.id), "x": int(a.x), "y": int(a.y), "state": a.state,
            "carrying": bool(a.carrying), "failed": bool(a.failed)}
