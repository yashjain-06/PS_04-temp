"""Naive baseline routes (owner: M3): they ignore obstacles, so robots must detour locally."""
from __future__ import annotations


def straight_route(src, dst) -> list:
    """Staircase line toward dst, always stepping along the axis with more distance left."""
    x, y = src
    path = []
    while (x, y) != tuple(dst):
        rx, ry = dst[0] - x, dst[1] - y
        if rx != 0 and (abs(rx) >= abs(ry) or ry == 0):
            x += 1 if rx > 0 else -1
        else:
            y += 1 if ry > 0 else -1
        path.append((x, y))
    return path


def random_route(src, dst, rng, grid=None) -> list:
    """Biased random walk: mostly toward dst, sometimes sideways. Finishes with a straight line."""
    x, y = src
    path, budget = [], 4 * (abs(dst[0] - x) + abs(dst[1] - y)) + 4
    while (x, y) != tuple(dst) and len(path) < budget:
        if rng.random() < 0.7:
            rx, ry = dst[0] - x, dst[1] - y
            if rx != 0 and (ry == 0 or rng.random() < abs(rx) / (abs(rx) + abs(ry))):
                x += 1 if rx > 0 else -1
            else:
                y += 1 if ry > 0 else -1
        else:
            dx, dy = ((1, 0), (-1, 0), (0, 1), (0, -1))[int(rng.integers(4))]
            if grid is None or grid.in_bounds(x + dx, y + dy):
                x, y = x + dx, y + dy
        path.append((x, y))
    return path + straight_route((x, y), dst)
