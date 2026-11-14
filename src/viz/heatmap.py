"""Traffic and pheromone heatmaps as PNG (owner: M4 + M3)."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


def save_heatmaps(snapshot: dict, out_png) -> None:
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
    for a, key, title in ((ax[0], "traffic", "Robot traffic (visits per cell)"), (ax[1], "pheromone", "Pheromone (recent building)")):
        a.imshow(np.array(snapshot[key]), cmap="magma", vmin=0)
        obs = np.zeros((snapshot["grid"]["height"], snapshot["grid"]["width"]))
        for x, y in snapshot.get("obstacles", []):
            obs[y, x] = 1
        a.imshow(np.ma.masked_where(obs == 0, obs), cmap="Greys", alpha=0.8, vmin=0, vmax=1)
        a.set_title(title)
        a.set_xticks([])
        a.set_yticks([])
    fig.tight_layout()
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=130)
    plt.close(fig)
