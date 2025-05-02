"""Seeding helpers so runs reproduce."""
from __future__ import annotations

import os
import random
from typing import Optional

DEFAULT_SEED = 913


def set_seed(seed: int = DEFAULT_SEED) -> int:
    """Seed Python's RNG and the hash seed. Returns the seed for logging."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    return seed


def seeded_rng(seed: Optional[int] = None) -> random.Random:
    # Isolated RNG so callers don't perturb the global one.
    return random.Random(DEFAULT_SEED if seed is None else seed)
