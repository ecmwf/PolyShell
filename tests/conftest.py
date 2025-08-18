"""Fixtures and test cases."""

from typing import Callable

from pytest_cases import fixture, parametrize_with_cases  # type: ignore


@fixture(scope="class")
@parametrize_with_cases("method", cases=".method_cases", scope="class")
def simplified(
    polygon: list[tuple[float, float]], method: Callable
) -> list[tuple[float, float]]:
    return method(polygon, eps=1e-6)
