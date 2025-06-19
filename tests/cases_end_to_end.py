"""Cases for end-to-end testing of reduce_polygon."""

import pickle
import random

from polygenerator import random_polygon as _random_polygon  # type: ignore
from pytest_cases import parametrize  # type: ignore

from polyshell.geometry import Polygon


class ComplexPolygons:
    """Complex polygon geometries used for end-to-end testing."""

    def case_ionian_sea(self) -> Polygon:
        """Polygon generated from the Ionian Sea."""
        with open("tests/data/ionian_polygon_points.pkl", "rb") as f:
            return Polygon.from_array(pickle.load(f))

    @parametrize("num_points,seed", [(1023, 0)])
    def case_random_polygon(self, num_points: int, seed: int) -> Polygon:
        """Generate a random polygon with given seed and number of points."""
        random.seed(seed)
        poly: list[tuple[float, float]] = _random_polygon(num_points)
        return Polygon.from_array(list(reversed(poly)))
