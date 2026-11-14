"""Single switch between the real model and the fake UI stand-in (owner: M4).

The real model is the default. Set the environment variable PS4_FAKE_MODEL=1 to use FakeModel
(UI work without the simulation). FakeModel is NOT decentralised and must never be demoed.
"""
import os

USE_REAL_MODEL = os.environ.get("PS4_FAKE_MODEL") != "1"


def make_model(params: dict):
    if USE_REAL_MODEL:
        from src.sim.model import build_model
        return build_model(**params)
    from src.sim.fake_model import FakeModel
    return FakeModel(**params)
