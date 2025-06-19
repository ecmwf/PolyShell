"""Tests for reduce_polygon."""

import pytest
from pytest_lazy_fixtures import lf
from shapely import is_valid  # type: ignore
from shapely.geometry import Polygon as ShapelyPolygon

from polyshell import reduce_polygon
from polyshell.geometry import Polygon

EPS = 1e-6

pytestmark = pytest.mark.parametrize(
    "polygon",
    [lf("ionian_sea"), lf("random_polygon")],
)


class TestCorrectness:
    """Test reduce_polygon for correctness."""

    def test_reduction(self, polygon: Polygon):
        """Check for errors when reducing a polygon."""
        reduce_polygon(polygon, epsilon=EPS)

    def test_intersections(self, polygon: Polygon):
        """Test reduced polygons for self-intersections."""
        simplified_polygon = reduce_polygon(polygon, epsilon=EPS)

        assert is_valid(ShapelyPolygon(simplified_polygon))

    def test_subset(self, polygon: Polygon):
        """Ensure reduced polygon vertices are a subset of the originals."""
        simplified_polygon = reduce_polygon(polygon, epsilon=EPS)

        original_vertices = polygon.points
        simplified_vertices = simplified_polygon.points

        assert all(map(lambda x: x in original_vertices, simplified_vertices))

    def test_encasement(self, polygon: Polygon):
        """Ensure reduced polygons contain the original in their interior."""
        simplified_polygon = reduce_polygon(polygon, epsilon=EPS)

        original_polygon_shapely = ShapelyPolygon(polygon)
        simplified_polygon_shapely = ShapelyPolygon(simplified_polygon)

        assert simplified_polygon_shapely.contains(original_polygon_shapely)
