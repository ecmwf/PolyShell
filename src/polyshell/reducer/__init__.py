from polyshell.geometry import Polygon

from .charshape import reduce_polygon_charshape
from .vw import reduce_polygon_vw
from .vw.loss_funcs import signed_area


def reduce_polygon(
    polygon: Polygon,
    epsilon: float,
    method: str = "visvalingam-whyatt",
) -> Polygon:
    """Reduce a polygon while retaining coverage."""
    match method:
        case "visvalingam-whyatt":
            return reduce_polygon_vw(polygon, epsilon, signed_area)
        case "charshape":
            return reduce_polygon_charshape(polygon, epsilon)
        case _:
            raise ValueError(f"Unknown method: {method}")
