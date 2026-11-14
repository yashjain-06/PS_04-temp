from src.sim.seeding import make_rng, set_seed
from src.utils.config import load_config
import random, numpy as np


def test_set_seed_reproducible():
    set_seed(1); a = (random.random(), np.random.rand())
    set_seed(1); b = (random.random(), np.random.rand())
    assert a == b


def test_streams_independent_but_reproducible():
    assert make_rng(1, "agents").random() == make_rng(1, "agents").random()
    assert make_rng(1, "agents").random() != make_rng(1, "aco").random()


def test_config_defaults_and_overrides():
    cfg = load_config(overrides={"simulation": {"n_agents": 30}})
    assert cfg["simulation"]["n_agents"] == 30
    assert cfg["simulation"]["seed"] == 42      # untouched default survives the merge
    cfg2 = load_config("configs/scaling.yaml")
    assert cfg2["agent_counts"] == [10, 20, 30, 50]
