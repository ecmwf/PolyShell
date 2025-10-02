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

"""Cases for end-to-end testing of reduce_polygon."""

import pickle
from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray
from shapely import Polygon as ShapelyPolygon


class CaseLarge:
    """Polygons with a very large number of vertices."""

    def case_ionian_sea(self) -> list[tuple[float, float]]:
        """Polygon generated from the Ionian Sea."""
        with open("tests/data/sea/ionian_sea.pkl", "rb") as f:
            return pickle.load(f)

    def case_afro_eurasia(self) -> list[tuple[float, float]]:
        """Polygon generated from the Afro-Eurasia land mass."""
        with open("tests/data/land/afro_eurasia.pkl", "rb") as f:
            return pickle.load(f)

    def case_americas(self) -> list[tuple[float, float]]:
        """Polygon generated from the Americas land mass."""
        with open("tests/data/land/americas.pkl", "rb") as f:
            return pickle.load(f)

    def case_antarctica(self) -> list[tuple[float, float]]:
        """Polygon generated from the Antarctic continent."""
        with open("tests/data/land/antarctica.pkl", "rb") as f:
            return pickle.load(f)

    def case_baffin_island(self) -> list[tuple[float, float]]:
        """Polygon generated from Baffin island."""
        with open("tests/data/land/baffin_island.pkl", "rb") as f:
            return pickle.load(f)

    def case_greenland(self) -> list[tuple[float, float]]:
        """Polygon generated from Greenland."""
        with open("tests/data/land/greenland.pkl", "rb") as f:
            return pickle.load(f)


class CaseSmall:
    """Polygons with a small number of vertices."""

    class CaseSelfIntersection:
        """Minimal polygons prone to self intersection."""

        def case_interlocking_teeth(self) -> list[tuple[float, float]]:
            """Two interlocking teeth with a narrow channel inbetween."""
            return [
                (0.0, 0.0),
                (0.0, 1.0),
                (0.25, 1.0),
                (0.05, 0.9),
                (0.25, 0.8),
                (0.25, 0.25),
                (0.75, 0.25),
                (0.75, 0.8),
                (0.15, 0.9),
                (0.75, 1.0),
                (1.0, 1.0),
                (1.0, 0.0),
                (0.0, 0.0),
            ]

    class CaseTypes:
        """Minimal polygons of various types."""

        def case_tuple_tuple(self) -> tuple[tuple[float, float], ...]:
            """A polygon as a tuple of tuples."""
            return (
                (0.0, 0.0),
                (0.0, 1.0),
                (0.5, 0.5),
                (1.0, 1.0),
                (1.0, 0.0),
                (0.0, 0.0),
            )

        def case_tuple_list(self) -> tuple[list[float], ...]:
            """A polygon as a tuple of lists."""
            return (
                [0.0, 0.0],
                [0.0, 1.0],
                [0.5, 0.5],
                [1.0, 1.0],
                [1.0, 0.0],
                [0.0, 0.0],
            )

        def case_list_tuple(self) -> list[tuple[float, float]]:
            """A polygon as a list of tuples."""
            return [
                (0.0, 0.0),
                (0.0, 1.0),
                (0.5, 0.5),
                (1.0, 1.0),
                (1.0, 0.0),
                (0.0, 0.0),
            ]

        def case_list_list(self) -> list[list[float]]:
            """A polygon as a list of lists."""
            return [
                [0.0, 0.0],
                [0.0, 1.0],
                [0.5, 0.5],
                [1.0, 1.0],
                [1.0, 0.0],
                [0.0, 0.0],
            ]

        def case_array(self) -> NDArray[np.floating]:
            """A polygon as a numpy array."""
            return np.array(
                [
                    [0.0, 0.0],
                    [0.0, 1.0],
                    [0.5, 0.5],
                    [1.0, 1.0],
                    [1.0, 0.0],
                    [0.0, 0.0],
                ]
            )

        def case_shapely(self) -> ShapelyPolygon:
            """A shapely Polygon."""
            return ShapelyPolygon(
                [
                    [0.0, 0.0],
                    [0.0, 1.0],
                    [0.5, 0.5],
                    [1.0, 1.0],
                    [1.0, 0.0],
                    [0.0, 0.0],
                ]
            )

        def case_sequence(self) -> Sequence[tuple[float, float]]:
            """A polygon as a custom type."""

            class CoordSequence(Sequence):
                def __init__(self, coords: list[tuple[float, float]]):
                    self.coords = coords

                def __len__(self) -> int:
                    return len(self.coords)

                def __getitem__(self, index: int) -> tuple[float, float]:
                    return self.coords[index]

            return CoordSequence(
                [
                    (0.0, 0.0),
                    (0.0, 1.0),
                    (0.5, 0.5),
                    (1.0, 1.0),
                    (1.0, 0.0),
                    (0.0, 0.0),
                ]
            )

    class CaseOrientation:
        def case_clockwise(self):
            return (
                (0.0, 0.0),
                (0.0, 1.0),
                (0.5, 0.5),
                (1.0, 1.0),
                (1.0, 0.0),
                (0.0, 0.0),
            )

        def case_counter_clockwise(self):
            return (
                (0.0, 0.0),
                (1.0, 0.0),
                (1.0, 1.0),
                (0.5, 0.5),
                (0.0, 1.0),
                (0.0, 0.0),
            )

    def case_null(self):
        return []

    def case_triangle(self):
        return [
            (0.0, 0.0),
            (0.0, 1.0),
            (1.0, 0.0),
            (0.0, 0.0),
        ]
