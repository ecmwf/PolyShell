"""Fixtures and test cases."""

from pytest_cases import fixture  # type: ignore

from polyshell import reduce_polygon
from polyshell.geometry import Polygon


@fixture(scope="class")
def simplified(polygon: Polygon) -> Polygon:
    return reduce_polygon(polygon, epsilon=1e-6)
