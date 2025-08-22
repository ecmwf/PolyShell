from enum import Enum, auto

from polyshell.geometry import Polygon

from .charshape import reduce_polygon_charshape
from .vw import reduce_polygon_vw
from .rdp import reduce_polygon_rdp
from .vw.loss_funcs import signed_area


class ReductionMethods(Enum):
    VisvalingamWhyatt = auto()
    Charshape = auto()
    RamerDouglasPeucker = auto()


def reduce_polygon(
    polygon: Polygon,
    epsilon: float,
    method: ReductionMethods = ReductionMethods.RamerDouglasPeucker,
) -> Polygon:
    """Reduce a polygon while retaining coverage."""
    match method:
        case ReductionMethods.VisvalingamWhyatt:
            return reduce_polygon_vw(polygon, epsilon, signed_area)
        case ReductionMethods.Charshape:
            return reduce_polygon_charshape(polygon, epsilon)
        case ReductionMethods.RamerDouglasPeucker:
            return reduce_polygon_rdp(polygon, epsilon, signed_area)
        case _:
            raise ValueError(f"Unknown method: {method}")
