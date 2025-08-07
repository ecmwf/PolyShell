"""Fixtures and test cases."""

from pytest_cases import fixture, parametrize_with_cases  # type: ignore

from polyshell import reduce_polygon
from polyshell.geometry import Polygon
from polyshell.reducer import ReductionMethods


@fixture(scope="class")
@parametrize_with_cases("method", cases=".method_cases", scope="class")
def simplified(polygon: Polygon, method: ReductionMethods) -> Polygon:
    return reduce_polygon(polygon, epsilon=1e-6, method=method)
