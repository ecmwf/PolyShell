"""Fixtures and test cases."""

from polyshell import ReductionMethod, ReductionMode, reduce_polygon
from pytest_cases import fixture, parametrize_with_cases  # type: ignore


@fixture(scope="class")
@parametrize_with_cases("method", cases=".method_cases", scope="class")
def simplified(
    polygon: list[tuple[float, float]], method: ReductionMethod
) -> list[tuple[float, float]]:
    return reduce_polygon(polygon, ReductionMode.EPSILON, 1e-6, method)
