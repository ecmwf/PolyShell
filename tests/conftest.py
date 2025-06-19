"""Fixtures for testing."""

import pickle

import pytest
from polyshell.geometry import Polygon


@pytest.fixture
def ionian_sea() -> Polygon:
    """Polygon generated from the Ionian Sea."""
    with open("tests/data/ionian_polygon_points.pkl", "rb") as f:
        return Polygon.from_array(pickle.load(f))
