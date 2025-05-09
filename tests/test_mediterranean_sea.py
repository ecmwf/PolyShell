import pickle

from shapely.geometry import Polygon

from polyshell import reduce_polygon


class TestPolygonReduction:
    def setup_method(self, method):
        with open("tests/data/ionian_polygon_points.pkl", "rb") as f:
            self.original_polygon = pickle.load(f)

    def test_group_and_product(self):
        original_polygon_shapely = Polygon(self.original_polygon)
        simplified_polygon = reduce_polygon(self.original_polygon)
        simplified_polygon_shapely = Polygon(simplified_polygon)

        # Check if the simplified polygon contains the original polygon
        assert simplified_polygon_shapely.contains(original_polygon_shapely)
