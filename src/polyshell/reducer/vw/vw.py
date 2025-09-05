"""Visvalingam-Whyatt line reduction algorithm."""

import heapq
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Iterable, Optional
from polyshell.reducer.utils import Logger
from polyshell.cli.kneepoint_detect import AdaptiveEpsilon

from rtree.index import Rtree

from polyshell.convex_hull import melkman_indices
from polyshell.geometry import (
    Geometry,
    Line,
    LineString,
    Polygon,
    Triangle,
)

from .loss_funcs import LossFunction

ID = 0  # ID for rtree

@dataclass(order=True)
class VWScore:
    """A score for a vertex in the Visvalingam-Whyatt algorithm."""

    sort_index: float = field(init=False)
    score: float
    current: int
    left: int
    right: int

    def __post_init__(self):
        self.sort_index = self.score


def data_stream(geoms: Iterable[Geometry]):
    for item in geoms:
        yield ID, item.bbox(), item


def worker_wraps(epsilon: float, loss_fn: LossFunction, logger : Logger, adaptive : bool):
    def worker(ls: LineString) -> LineString:
        return vw_preserve(ls, epsilon, loss_fn, logger, adaptive)

    return worker


def reduce_polygon_vw(
    polygon: Polygon,
    epsilon: float,
    loss_fn: LossFunction,
    logger : Logger,
    adaptive:bool,
    max_workers: Optional[int],
) -> Polygon:
    """Reduce a polygon while retaining coverage."""
    vertices = melkman_indices(polygon)
    segments = [
        polygon[start : end + 1] for start, end in zip(vertices[:-1], vertices[1:])
    ]

    with ThreadPoolExecutor(max_workers) as tpe:
        reduced_segments = tpe.map(worker_wraps(epsilon, loss_fn, logger, adaptive), segments)

    return Polygon.merge(reduced_segments)


def vw_preserve(
    polygon_points: LineString, epsilon: float, loss_fn: LossFunction, logger : Logger, adaptive : bool
) -> LineString:
    """Visvalingam-Whyatt line reduction algorithm adapted to prevent crossings."""
    if len(polygon_points) < 3 or epsilon <= 0:
        return polygon_points

    max_points = len(polygon_points)

    tree = Rtree(data_stream(polygon_points.lines()))

    adjacent = [(i - 1, i + 1) for i in range(max_points)]

    pq = [
        VWScore(
            score,
            current=i + 1,
            left=i,
            right=i + 2,
        )
        for i, triangle in enumerate(polygon_points.triangles())
        if (score := loss_fn(triangle)) >= 0
    ]
    heapq.heapify(pq)

    loss = 0
    while len(pq):
        smallest = heapq.heappop(pq)

        if smallest.score > epsilon:
            break

        if logger.query(smallest.score) and adaptive:
            break

        # Check if the score is invalidated
        left, right = adjacent[smallest.current]
        if left != smallest.left or right != smallest.right:
            continue

        # Check for self-intersection
        if tree_intersect(tree, smallest, polygon_points):
            # Skip this point
            continue

        # Update adjacency list
        ll, _ = adjacent[left]
        _, rr = adjacent[right]
        adjacent[left] = (ll, right)
        adjacent[right] = (left, rr)
        adjacent[smallest.current] = (0, 0)

        # Reconnect vertices
        left_point = polygon_points[left]
        right_point = polygon_points[right]
        new_line = Line((left_point, right_point))
        tree.insert(ID, new_line.bbox(), new_line)

        # Update adjacent triangles
        recompute_triangles(
            polygon_points,
            pq,
            ll,
            left,
            right,
            rr,
            max_points,
            loss_fn,
        )

        # Update loss
        loss += smallest.score
        logger.update(smallest.score)
    # Filter out any deleted points
    return LineString(
        [point for point, adj in zip(polygon_points, adjacent) if adj != (0, 0)]
    )


def recompute_triangles(
    points: LineString,
    pq: list[VWScore],
    ll: int,
    left: int,
    right: int,
    rr: int,
    max: int,
    loss_fn: LossFunction,
):
    choices = [(ll, left, right), (left, right, rr)]
    for ai, current_point, bi in choices:
        if not (0 <= ai < max and 0 <= bi < max):
            continue  # out of bounds

        score = loss_fn(Triangle((points[ai], points[current_point], points[bi])))
        if score < 0:
            continue  # do not push negative areas

        v = VWScore(
            score,
            current=current_point,
            left=ai,
            right=bi,
        )
        heapq.heappush(pq, v)


def tree_intersect(tree: Rtree, triangle: VWScore, points: LineString) -> bool:
    """Check if removal of a triangle causes a self-intersection."""
    new_segment_start = points[triangle.left]
    new_segment_end = points[triangle.right]

    new_segment = Line((new_segment_start, new_segment_end))

    bounding_rect = Triangle(
        (points[triangle.left], points[triangle.current], points[triangle.right])
    ).bbox()

    candidates = tree.intersection(bounding_rect, objects=True)

    for candidate_item in candidates:
        candidate: Line = candidate_item.object  # type: ignore
        candidate_start, candidate_end = candidate
        if (
            candidate_start != new_segment_start
            and candidate_start != new_segment_end
            and candidate_end != new_segment_start
            and candidate_end != new_segment_end
            and new_segment.intersects(candidate)
        ):
            return True

    else:
        return False
