"""One robot per cell and right-of-way (owner: M2).

Right of way: a robot carrying a block beats an empty one; ties go to the lower id.
The lower-priority robot yields (side-steps) after one blocked tick; the higher-priority one waits
`patience` ticks and then backs off anyway, so no pair can wait on each other forever.
"""
from __future__ import annotations


def priority(a) -> tuple:
    return (0 if a.carrying else 1, a.id)


def should_yield(a, other, waited: int, patience: int) -> bool:
    return waited >= (1 if priority(a) > priority(other) else patience)
