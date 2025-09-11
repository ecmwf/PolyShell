from collections.abc import Sequence

__all__ = ["reduce_polygon_char", "reduce_polygon_rdp", "reduce_polygon_rdp"]

SupportsIntoVec = Sequence[tuple[float, float]]

def reduce_polygon_char(
    polygon: SupportsIntoVec, eps: float, len: int
) -> list[list[float]]:
    """Reduce a polygon while retaining coverage."""

def reduce_polygon_rdp(polygon: SupportsIntoVec, eps: float) -> list[list[float]]:
    """Reduce a polygon while retaining coverage."""

def reduce_polygon_vw(
    polygon: SupportsIntoVec, eps: float, len: int
) -> list[list[float]]:
    """Reduce a polygon while retaining coverage."""
