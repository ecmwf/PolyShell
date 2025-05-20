"""Utilities for polyshell."""


def cross_2d(x, y):
    """Compute the two-dimensional cross product."""
    return x[..., 0] * y[..., 1] - x[..., 1] * y[..., 0]
