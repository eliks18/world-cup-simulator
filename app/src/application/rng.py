"""Random provider module."""

import random

import numpy as np


class RandomProvider:
    """Concrete wrapper holding a NumPy Generator and a stdlib Random.

    Exposes exactly two operations currently needed by the match simulator:
    a Poisson sampler and a uniform float sampler in [0, 1).
    """

    def __init__(self, numpy_rng: np.random.Generator, stdlib_rng: random.Random):
        self._numpy_rng = numpy_rng
        self._stdlib_rng = stdlib_rng

    def poisson(self, lam: float) -> int:
        """Sample from a Poisson distribution with mean ``lam``."""
        return self._numpy_rng.poisson(lam)

    def uniform(self) -> float:
        """Return a uniform float in [0, 1)."""
        return self._stdlib_rng.uniform(0.0, 1.0)
