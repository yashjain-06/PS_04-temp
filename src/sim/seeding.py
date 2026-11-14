"""Global seed control for reproducible runs (owner: M4)."""
from __future__ import annotations

import random
import zlib

import numpy as np


def set_seed(seed: int) -> None:
    """Seed Python's `random` and NumPy's global RNG. Call once at the start of every run."""
    random.seed(seed)
    np.random.seed(seed)


def make_rng(seed: int, stream: str = "") -> np.random.Generator:
    """Independent, reproducible RNG per component (e.g. 'agents', 'aco', 'failure').

    Different streams stay uncorrelated, and adding randomness in one module
    does not change the results of another.
    """
    offset = zlib.crc32(stream.encode()) if stream else 0
    return np.random.default_rng([seed, offset])
