from concurrent.futures import ThreadPoolExecutor
from enum import Enum, auto
from typing import Optional, overload

from polyshell.convex_hull import melkman_indices
from polyshell.geometry import LineString, Polygon

from .loss_funcs import LossFunction
from .vw import VWLineString


class VWRunningMode(Enum):
    Serial = auto()
    Parallel = auto()


@overload
def reduce_polygon_vw(poly: Polygon, eps: float, loss_fn: LossFunction) -> Polygon:
    pass


@overload
def reduce_polygon_vw(poly: Polygon, min_len: int, loss_fn: LossFunction) -> Polygon:
    pass


def worker_wraps(eps: float, min_len: int):
    def worker(state: VWLineString):
        state.reduce(eps, min_len)

    return worker


def init_vw_states(
    poly: Polygon, loss_fn: LossFunction, mode: VWRunningMode
) -> list[VWLineString]:
    hull_points = melkman_indices(poly)
    segments = [
        poly[start : end + 1] for start, end in zip(hull_points[:-1], hull_points[1:])
    ]

    if mode is VWRunningMode.Serial:
        segments = [LineString.merge(segments)]

    return [VWLineString(ls, loss_fn) for ls in segments]


def reduce_states_vw(
    vw_states: list[VWLineString],
    eps: float,
    min_sec_len: int,
    max_workers: Optional[int] = None,
):
    # If running mode is serial number of states is one
    with ThreadPoolExecutor(max_workers) as tpe:
        tpe.map(worker_wraps(eps, min_sec_len), vw_states)


def merge_states_vw(vw_states: list[VWLineString]) -> Polygon:
    return Polygon.merge([state.into() for state in vw_states])


# General procedure:
# - Init states
# - Perform reduction
# - Repeat as necessary
# - Merge into Polygon


# Options:
# - Store past losses in a vec and use adjacent to store removal order
#   - Post-process to zip LineStrings as desired (works with objective min_len provided we overshoot <- use adaptive + backtrack)

# Profiling:
# - How much faster is Rayon for our test set?
# - What is the cost of storing removal order and loss vec?
# -> If cost is low
