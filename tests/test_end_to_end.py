"""End-to-end testing for reduce_polygon."""

from pytest_cases import fixture, parametrize_with_cases  #  type: ignore
from shapely import is_valid  # type: ignore
from shapely.geometry import Polygon as ShapelyPolygon

from polyshell.geometry import Polygon

from .cases_end_to_end import ComplexPolygons


class TestRequirements:
    """Test reduce_polygon against requirements."""

    @fixture(scope="class")
    @parametrize_with_cases("polygon", cases=ComplexPolygons, scope="class")
    def polygon(self, polygon: Polygon) -> Polygon:
        return polygon

    def test_reduction(self, simplified: Polygon):
        """Check for errors when reducing a polygon."""

    def test_intersections(self, simplified: Polygon):
        """Test reduced polygons for self-intersections."""
        assert is_valid(ShapelyPolygon(simplified))

    def test_subset(self, polygon: Polygon, simplified: Polygon):
        """Ensure reduced polygon vertices are a subset of the originals."""
        original_vertices = polygon.points
        simplified_vertices = simplified.points

        assert all(map(lambda pt: pt in original_vertices, simplified_vertices))

    def test_containment(self, polygon: Polygon, simplified: Polygon):
        """Ensure reduced polygons contain the original in their interior."""
        original_shapely = ShapelyPolygon(polygon)
        simplified_shapely = ShapelyPolygon(simplified)

        assert simplified_shapely.contains(original_shapely)
