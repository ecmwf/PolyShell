import pickle

from shapely.geometry import Polygon as ShapelyPolygon

from polyshell import reduce_polygon
from polyshell.geometry import Polygon


class TestPolygonReduction:
    def setup_method(self, method):
        with open("tests/data/ionian_polygon_points.pkl", "rb") as f:
            self.polygon_array = pickle.load(f)

    def test_group_and_product(self):
        original_polygon = Polygon.from_array(self.polygon_array)
        simplified_polygon = reduce_polygon(original_polygon, epsilon=1e-6)

        original_polygon_shapely = ShapelyPolygon(self.polygon_array)
        simplified_polygon_shapely = ShapelyPolygon(simplified_polygon)

        # Check if the simplified polygon contains the original polygon
        assert simplified_polygon_shapely.contains(original_polygon_shapely)
