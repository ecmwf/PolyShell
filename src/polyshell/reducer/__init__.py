from enum import Enum, auto

from polyshell.geometry import Polygon
from .charshape import reduce_polygon_charshape
from .vw import reduce_polygon_vw
from .vw.loss_funcs import signed_area
from polyshell.reducer.utils import Logger
class ReductionMethods(Enum):
    VisvalingamWhyatt = auto()
    Charshape = auto()



def reduce_polygon(
    polygon: Polygon,
    epsilon: float,
    logger : Logger | None = None,
    method: ReductionMethods = ReductionMethods.VisvalingamWhyatt,
    adaptive : bool = True) -> Polygon | None:
    """Reduce a polygon while retaining coverage."""
    match method:
        case ReductionMethods.VisvalingamWhyatt:
            if logger is None:
                logger = Logger(len(polygon))
            return reduce_polygon_vw(polygon, epsilon, signed_area, logger, adaptive, 10)
        case ReductionMethods.Charshape:
            if logger is None:
                logger = Logger(len(polygon))
            #return reduce_polygon_charshape(polygon, epsilon, logger, adaptive)
        case _:
            raise ValueError(f"Unknown method: {method}")
