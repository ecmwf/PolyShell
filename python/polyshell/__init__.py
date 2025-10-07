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


from collections.abc import Sequence
from enum import Enum
from typing import Literal, overload

from polyshell._polyshell import (
    __version__,
    reduce_polygon_char,
    reduce_polygon_rdp,
    reduce_polygon_vw,
)

__all__ = [
    "ReductionMethod",
    "ReductionMode",
    "reduce_polygon",
    "reduce_polygon_eps",
    "reduce_polygon_len",
    "reduce_polygon_auto",
    "__version__",
]


Polygon = Sequence[tuple[float, float]]


class NullClass:
    pass


class ReductionMethod(str, Enum):
    CHARSHAPE = "charshape"
    RDP = "rdp"
    VW = "vw"


class ReductionMode(str, Enum):
    EPSILON = "epsilon"
    LENGTH = "length"
    AUTO = "auto"


# Feature gates
try:
    from shapely import Polygon as ShapelyPolygon

    Polygon = Polygon | ShapelyPolygon
except ImportError:
    ShapelyPolygon = NullClass

try:
    from numpy import ndarray
    from numpy.typing import NDArray

    Polygon = Polygon | NDArray[float]
except ImportError:
    ndarray = NullClass


def into_polygon(obj: any) -> Sequence[tuple[float, float]]:
    """Cast a polygon object into a supported type."""
    match obj:
        case [*_] as seq:
            return seq
        case ndarray() as arr:
            return arr
        case ShapelyPolygon(exterior=exterior):
            return exterior.coords
        case _:
            raise TypeError(
                f"{type(obj)} cannot be interpreted as Polygon object {ShapelyPolygon}"
            )


@overload
def reduce_polygon(
    polygon: Polygon,
    mode: Literal[ReductionMode.EPSILON],
    epsilon: float,
    method: ReductionMethod,
) -> list[list[float]]:
    pass


@overload
def reduce_polygon(
    polygon: Polygon,
    mode: Literal[ReductionMode.LENGTH],
    length: int,
    method: ReductionMethod,
) -> list[list[float]]:
    pass


@overload
def reduce_polygon(
    polygon: Polygon, mode: Literal[ReductionMode.AUTO], method: ReductionMethod
) -> list[list[float]]:
    pass


def reduce_polygon(
    polygon: Polygon,
    mode: ReductionMode,
    *args,
    **kwargs,
) -> list[list[float]]:
    match mode:
        case ReductionMode.EPSILON:
            return reduce_polygon_eps(polygon, *args, **kwargs)
        case ReductionMode.LENGTH:
            return reduce_polygon_len(polygon, *args, **kwargs)
        case ReductionMode.AUTO:
            return reduce_polygon_auto(polygon, *args, **kwargs)
        case _:
            raise ValueError(
                f"Unknown reduction mode. Must be one of {[e.value for e in ReductionMode]}"
            )


def reduce_polygon_eps(
    polygon: Polygon, epsilon: float, method: ReductionMethod
) -> list[list[float]]:
    polygon = into_polygon(polygon)
    match method:
        case ReductionMethod.CHARSHAPE:
            return reduce_polygon_char(polygon, epsilon, len(polygon))
        case ReductionMethod.RDP:
            return reduce_polygon_rdp(polygon, epsilon)
        case ReductionMethod.VW:
            return reduce_polygon_vw(polygon, epsilon, 0)
        case _:
            raise ValueError(
                f"Unknown reduction method. Must be one of {[e.value for e in ReductionMethod]}"
            )


def reduce_polygon_len(
    polygon: Polygon,
    length: int,
    method: ReductionMethod,
) -> list[list[float]]:
    polygon = into_polygon(polygon)
    match method:
        case ReductionMethod.CHARSHAPE:
            return reduce_polygon_char(polygon, 0.0, length)  # maximum length
        case ReductionMethod.RDP:
            raise NotImplementedError("Fixed length is not implemented for RDP")
        case ReductionMethod.VW:
            # minimum length
            return reduce_polygon_vw(polygon, float("inf"), length)
        case _:
            raise ValueError(
                f"Unknown reduction method. Must be one of {[e.value for e in ReductionMethod]}"
            )


def reduce_polygon_auto(polygon: Polygon, method: ReductionMethod) -> list[list[float]]:
    polygon = into_polygon(polygon)
    match method:
        case ReductionMethod.CHARSHAPE:
            raise NotImplementedError
        case ReductionMethod.RDP:
            raise NotImplementedError
        case ReductionMethod.VW:
            raise NotImplementedError
        case _:
            raise ValueError(
                f"Unknown reduction method. Must be one of {[e.value for e in ReductionMethod]}"
            )
