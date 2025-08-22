from concurrent.futures import ThreadPoolExecutor
from enum import auto, Enum
from typing import overload, Optional

from .loss_funcs import LossFunction
from .rdp import RDPLineString
from polyshell.convex_hull import melkman_indices
from polyshell.geometry import LineString, Polygon


class RDPRunningMode(Enum):
    Serial = auto()
    Parallel = auto()


def reduce_polygon_rdp(poly: Polygon, eps: float, loss_fn: LossFunction) -> Polygon:
    rdp_states = init_rdp_states(poly, loss_fn, RDPRunningMode.Serial)
    reduce_states_rdp(rdp_states, eps, 2)
    return merge_states_rdp(rdp_states)


def worker_wraps(eps: float, min_len: int):
    def worker(state: RDPLineString):
        state.reduce(eps, min_len)

    return worker


def init_rdp_states(poly: Polygon, loss_fn: LossFunction, mode: RDPRunningMode) -> list[RDPLineString]:
    hull_points = melkman_indices(poly)
    segments = [
        poly[start : end + 1] for start, end in zip(hull_points[:-1], hull_points[1:])
    ]

    # if mode is RDPRunningMode.Serial:
    #     segments = [LineString.merge(segments)]

    return [RDPLineString(ls, loss_fn) for ls in segments]


def reduce_states_rdp(rdp_states: list[RDPLineString], eps: float, min_sec_len: int, max_workers: Optional[int] = None):
    # If running mode is serial number of states is one
    with ThreadPoolExecutor(max_workers) as tpe:
        tpe.map(worker_wraps(eps, min_sec_len), rdp_states)


def merge_states_rdp(rdp_states: list[RDPLineString]) -> Polygon:
    return Polygon.merge([state.into() for state in rdp_states])
