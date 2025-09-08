from enum import Enum
from typing import Literal, overload

from pydantic import validate_call

from polyshell._polyshell import *

Polygon = list[tuple[float, float]]


class ReductionMethod(str, Enum):
    CHARSHAPE = "charshape"
    RDP = "rdp"
    VW = "vw"


class ReductionMode(str, Enum):
    EPSILON = "epsilon"
    LENGTH = "length"
    AUTO = "auto"


@overload
def reduce_polygon(
    polygon: Polygon,
    mode: Literal[ReductionMode.EPSILON],
    epsilon: float,
    method: ReductionMethod,
) -> Polygon:
    pass


@overload
def reduce_polygon(
    polygon: Polygon,
    mode: Literal[ReductionMode.LENGTH],
    length: int,
    method: ReductionMethod,
) -> Polygon:
    pass


@overload
def reduce_polygon(
    polygon: Polygon, mode: Literal[ReductionMode.AUTO], method: ReductionMethod
) -> Polygon:
    pass


def reduce_polygon(
    polygon: Polygon,
    mode: ReductionMode,
    *args,
    **kwargs,
) -> Polygon:
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


@validate_call
def reduce_polygon_eps(
    polygon: Polygon, epsilon: float, method: ReductionMethod
) -> Polygon:
    match method:
        case ReductionMethod.CHARSHAPE:
            return reduce_polygon_char(polygon, epsilon, len(polygon))
        case ReductionMethod.RDP:
            return reduce_polygon_rdp(polygon, epsilon)
        case ReductionMethod.VW:
            return reduce_polygon_vw(polygon, epsilon, 0)


@validate_call
def reduce_polygon_len(
    polygon: Polygon,
    length: int,
    method: ReductionMethod,
) -> Polygon:
    match method:
        case ReductionMethod.CHARSHAPE:
            return reduce_polygon_char(polygon, 0.0, length)  # maximum length
        case ReductionMethod.RDP:
            raise NotImplementedError
        case ReductionMethod.VW:
            return reduce_polygon_vw(polygon, float("inf"), length)  # minimum length


@validate_call
def reduce_polygon_auto(polygon: Polygon, method: ReductionMethod) -> Polygon:
    match method:
        case ReductionMethod.CHARSHAPE:
            raise NotImplementedError
        case ReductionMethod.RDP:
            raise NotImplementedError
        case ReductionMethod.VW:
            raise NotImplementedError
