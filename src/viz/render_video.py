"""Record a build as a GIF (owner: M4). Uses the same model the web app uses."""
from __future__ import annotations

from pathlib import Path

import imageio.v2 as imageio

from src.sim.factory import make_model
from src.viz.render_frames import render_frame


def record_gif(params: dict, path: str | Path, every: int = 2, cell: int = 20, fps: int = 12,
               show_traffic: bool = False, hold_last: int = 12) -> int:
    """Run the model and save a GIF with one frame every `every` ticks. Returns the number of frames."""
    model = make_model(params)
    frames = [render_frame(model.snapshot(), cell, show_traffic)]
    while not model.build_complete() and model.tick < params.get("max_ticks", 3000):
        model.step()
        if model.tick % every == 0:
            frames.append(render_frame(model.snapshot(), cell, show_traffic))
    frames += [render_frame(model.snapshot(), cell, show_traffic)] * hold_last      # linger on the finished build
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(path, frames, duration=1000 / fps, loop=0)
    return len(frames)
