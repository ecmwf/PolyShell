"""Fixtures for testing."""

import pickle
import random

import pytest
from polygenerator import random_polygon as _random_polygon  # type: ignore
from polyshell.geometry import Polygon


@pytest.fixture
def ionian_sea() -> Polygon:
    """Polygon generated from the Ionian Sea."""
    with open("tests/data/ionian_polygon_points.pkl", "rb") as f:
        return Polygon.from_array(pickle.load(f))


@pytest.fixture(params=[(1023, 0)])
def random_polygon(request: pytest.FixtureRequest) -> Polygon:
    """Generate a random polygon with given seed and number of points."""
    num_points, seed = request.param
    random.seed(seed)
    poly: list[tuple[float, float]] = _random_polygon(num_points)
    return Polygon.from_array(list(reversed(poly)))
