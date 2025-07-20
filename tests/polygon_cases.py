"""Cases for end-to-end testing of reduce_polygon."""

import pickle
import random

from polygenerator import random_polygon  # type: ignore
from pytest_cases import parametrize  # type: ignore

from polyshell.geometry import Polygon


class CaseLarge:
    """Polygons with a very large number of vertices."""

    def case_ionian_sea(self) -> Polygon:
        """Polygon generated from the Ionian Sea."""
        with open("tests/data/ionian_polygon_points.pkl", "rb") as f:
            return Polygon.from_array(pickle.load(f))

    @parametrize("num_points,seed", [(1000, 0)])
    def case_random_polygon(self, num_points: int, seed: int) -> Polygon:
        """Generate a random polygon with given seed and number of points."""
        random.seed(seed)
        poly: list[tuple[float, float]] = random_polygon(
            num_points
        )  # This function is very slow
        poly.append(poly[0])
        return Polygon.from_array(list(reversed(poly)))


class CaseSmall:
    """Polygons with a small number of vertices."""

    class CaseSelfIntersection:
        """Minimal polygons prone to self intersection."""

        def case_interlocking_teeth(self) -> Polygon:
            """Two interlocking teeth with a narrow channel inbetween."""
            return Polygon.from_array(
                [
                    (0.0, 0.0),
                    (0.0, 1.0),
                    (0.25, 1.0),
                    (0.05, 0.9),
                    (0.25, 0.8),
                    (0.25, 0.25),
                    (0.75, 0.25),
                    (0.75, 0.8),
                    (0.15, 0.9),
                    (0.75, 1.0),
                    (1.0, 1.0),
                    (1.0, 0.0),
                    (0.0, 0.0),
                ]
            )
