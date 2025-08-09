"""Visvalingam-Whyatt line reduction algorithm."""

import heapq
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Iterable, Optional

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


class VWState:
    def __init__(self, orig: LineString, loss_fn: LossFunction):
        self.orig = orig
        self.loss_fn = loss_fn

        self.max = len(orig)
        self.tree = Rtree(data_stream(orig.lines()))
        self.adjacent = [(i - 1, i + 1) for i in range(len(orig))]
        self.pq = [
            VWScore(
                score,
                current=i + 1,
                left=i,
                right=i + 2,
            )
            for i, triangle in enumerate(orig.triangles())
            if (score := loss_fn(triangle)) >= 0
        ]
        heapq.heapify(self.pq)
        self.loss = 0.0

    def into(self) -> LineString:
        return LineString(
            [point for point, adj in zip(self.orig, self.adjacent) if adj != (0, 0)]
        )

    def reduce(self, epsilon: float) -> None:
        while len(self.pq):
            smallest = heapq.heappop(self.pq)

            if smallest.score > epsilon:
                # smallest is not removed so return to the heap
                heapq.heappush(self.pq, smallest)
                break

            # Check if the score is invalidated
            left, right = self.adjacent[smallest.current]
            if left != smallest.left or right != smallest.right:
                continue

            # Check for self-intersection
            if self.tree_intersect(smallest):
                # Skip this point
                continue

            # Update adjacency list
            ll, _ = self.adjacent[left]
            _, rr = self.adjacent[right]
            self.adjacent[left] = (ll, right)
            self.adjacent[right] = (left, rr)
            self.adjacent[smallest.current] = (0, 0)

            # Reconnect vertices
            left_point = self.orig[left]
            right_point = self.orig[right]
            new_line = Line((left_point, right_point))
            self.tree.insert(ID, new_line.bbox(), new_line)

            # Update adjacent triangles
            self.recompute_triangles(ll, left, right, rr)

            # Update loss
            self.loss += smallest.score

    def tree_intersect(self, triangle: VWScore) -> bool:
        """Check if removal of a triangle causes a self-intersection."""
        new_segment_start = self.orig[triangle.left]
        new_segment_end = self.orig[triangle.right]

        new_segment = Line((new_segment_start, new_segment_end))

        bounding_rect = Triangle(
            (
                self.orig[triangle.left],
                self.orig[triangle.current],
                self.orig[triangle.right],
            )
        ).bbox()

        candidates = self.tree.intersection(bounding_rect, objects=True)

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

    def recompute_triangles(
        self,
        ll: int,
        left: int,
        right: int,
        rr: int,
    ):
        choices = [(ll, left, right), (left, right, rr)]
        for ai, current_point, bi in choices:
            if not (0 <= ai < self.max and 0 <= bi < self.max):
                continue  # out of bounds

            score = self.loss_fn(
                Triangle((self.orig[ai], self.orig[current_point], self.orig[bi]))
            )
            if score < 0:
                continue  # do not push negative areas

            v = VWScore(
                score,
                current=current_point,
                left=ai,
                right=bi,
            )
            heapq.heappush(self.pq, v)


def reduce_polygon_vw(
        polygon: Polygon,
        epsilon: float,
        loss_fn: LossFunction,
        max_workers: Optional[int] = None,
) -> Polygon:
    """Reduce a polygon while retaining coverage."""
    vertices = melkman_indices(polygon)
    segments = [
        polygon[start : end + 1] for start, end in zip(vertices[:-1], vertices[1:])
    ]
    vw_states = [VWState(ls, loss_fn) for ls in segments]

    with ThreadPoolExecutor(max_workers) as tpe:
        tpe.map(worker_wraps(epsilon), vw_states)

    return Polygon.merge([state.into() for state in vw_states])


def data_stream(geoms: Iterable[Geometry]):
    for item in geoms:
        yield ID, item.bbox(), item


def worker_wraps(epsilon: float):
    def worker(state: VWState):
        state.reduce(epsilon)

    return worker
