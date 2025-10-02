#
# Copyright 2025- European Centre for Medium-Range Weather Forecasts (ECMWF)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation nor
# does it submit to any jurisdiction.
#
# Copyright 2025- Niall Oswald and Kenneth Martin and Jo Wayne Tan
#

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
        if isinstance(polygon, ShapelyPolygon):
            original_set = set(map(lambda v: tuple(v), list(polygon.exterior.coords)))
        else:
            original_set = set(map(lambda v: tuple(v), polygon))
        simplified_set = set(map(lambda v: tuple(v), simplified))

        assert simplified_set <= original_set

    def test_containment(
        self, polygon: list[tuple[float, float]], simplified: list[tuple[float, float]]
    ):
        """Ensure reduced polygons contain the original in their interior."""
        original_shapely = ShapelyPolygon(polygon)
        simplified_shapely = ShapelyPolygon(simplified)

        if isinstance(polygon, ShapelyPolygon):
            length = polygon.length
        else:
            length = len(polygon)

        # The null polygon cannot contain itself
        if length:
            assert simplified_shapely.contains(original_shapely)
