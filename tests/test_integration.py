"""End-to-end testing for reduce_polygon."""

from pytest_cases import fixture, parametrize_with_cases  # type: ignore
from shapely import is_valid  # type: ignore
from shapely.geometry import Polygon as ShapelyPolygon


class TestRequirements:
    """Test reduce_polygon against requirements."""

    @fixture(scope="class")
    @parametrize_with_cases("polygon", cases=".polygon_cases", scope="class")
    def polygon(self, polygon: list[tuple[float, float]]) -> list[tuple[float, float]]:
        return polygon

    def test_reduction(self, simplified: list[tuple[float, float]]):
        """Check for errors when reducing a polygon."""

    def test_intersections(self, simplified: list[tuple[float, float]]):
        """Test reduced polygons for self-intersections."""
        assert is_valid(ShapelyPolygon(simplified))

    def test_subset(
        self, polygon: list[tuple[float, float]], simplified: list[tuple[float, float]]
    ):
        """Ensure reduced polygon vertices are a subset of the originals."""
        original_set = set(map(lambda v: tuple(v), polygon))
        simplified_set = set(map(lambda v: tuple(v), simplified))

        assert simplified_set <= original_set

    def test_containment(
        self, polygon: list[tuple[float, float]], simplified: list[tuple[float, float]]
    ):
        """Ensure reduced polygons contain the original in their interior."""
        original_shapely = ShapelyPolygon(polygon)
        simplified_shapely = ShapelyPolygon(simplified)

        assert simplified_shapely.contains(original_shapely)
