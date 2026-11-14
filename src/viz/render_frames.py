"""Draw a snapshot as an RGB image with plain numpy (owner: M4). No GUI or font dependencies."""
from __future__ import annotations

import numpy as np

BG, GRID = (250, 251, 252), (225, 228, 232)
GHOST, BLOCK, DEPOT, ROCK = (200, 214, 250), (107, 114, 128), (245, 158, 11), (71, 85, 105)
STATE = {"seek": (47, 111, 237), "carry": (22, 163, 74), "place": (168, 85, 247), "return": (14, 165, 165)}
FAILED = (220, 38, 38)


def _fill(img, x, y, cell, color, inset=0):
    img[y * cell + inset:(y + 1) * cell - inset, x * cell + inset:(x + 1) * cell - inset] = color


def render_frame(snap: dict, cell: int = 20, show_traffic: bool = False) -> np.ndarray:
    W, H = snap["grid"]["width"], snap["grid"]["height"]
    img = np.empty((H * cell, W * cell, 3), dtype=np.uint8)
    img[:] = BG
    if show_traffic:
        for y, row in enumerate(snap.get("traffic", [])):
            for x, v in enumerate(row):
                if v > 0:
                    _fill(img, x, y, cell, tuple(int(BG[i] * (1 - 0.75 * v) + (220, 38, 38)[i] * 0.75 * v) for i in range(3)))
    for y, row in enumerate(snap.get("pheromone", [])):
        for x, v in enumerate(row):
            if v > 0.05:
                _fill(img, x, y, cell, tuple(int(BG[i] * (1 - 0.5 * v) + DEPOT[i] * 0.5 * v) for i in range(3)))
    img[::cell, :] = GRID
    img[:, ::cell] = GRID
    for x, y in snap.get("obstacles", []):
        _fill(img, x, y, cell, ROCK)
    for x, y, *_ in snap["blueprint"]:
        _fill(img, x, y, cell, GHOST, inset=2)
    for x, y, *_ in snap["structure"]:
        _fill(img, x, y, cell, BLOCK, inset=1)
    for x, y in snap["depots"]:
        _fill(img, x, y, cell, DEPOT, inset=3)
    for a in snap["agents"]:
        cx, cy, r = a["x"] * cell + cell // 2, a["y"] * cell + cell // 2, max(2, int(cell * 0.32))
        if a["failed"]:
            for d in range(-r, r + 1):
                for xx, yy in ((cx + d, cy + d), (cx + d, cy - d)):
                    img[max(0, yy - 1):yy + 1, max(0, xx - 1):xx + 1] = FAILED
            continue
        yy, xx = np.ogrid[:img.shape[0], :img.shape[1]]
        img[(xx - cx) ** 2 + (yy - cy) ** 2 <= r * r] = STATE.get(a["state"], (0, 0, 0))
        if a["carrying"]:
            img[cy - r // 2:cy + r // 2, cx - r // 2:cx + r // 2] = (255, 255, 255)
    return img
