from polyshell.geometry import Polygon

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
        case _:
            raise ValueError(f"Unknown method: {method}")
