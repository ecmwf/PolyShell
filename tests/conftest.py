"""Fixtures and test cases."""

from polyshell import reduce_polygon
from pytest_cases import fixture  # type: ignore


@fixture(scope="class")
def simplified(polygon: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return reduce_polygon(polygon, epsilon=1e-6)
