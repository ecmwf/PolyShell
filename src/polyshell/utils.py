"""Utilities for polyshell."""

import numpy as np


def cross_2d(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Compute the two-dimensional cross product."""
    return x[..., 0] * y[..., 1] - x[..., 1] * y[..., 0]
