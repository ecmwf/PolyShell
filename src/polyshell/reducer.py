import heapq
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Iterable

from rtree.index import Rtree
from scipy.spatial import ConvexHull

from polyshell.geometry import Geometry, Line, LineString, Polygon, Triangle

ID = 0


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
        yield (ID, item.bbox(), item)


def worker_wraps(epsilon: float):
    def worker(ls: LineString) -> LineString:
        return vw_preserve(ls, epsilon)

    return worker


def reduce_polygon(
    polygon_points: Polygon, epsilon: float, max_workers: int
) -> Polygon:
    """Reduce a polygon while retaining coverage."""
    # Slice into LineStrings
    vertices = ConvexHull(polygon_points.to_array()).vertices[::-1]
    vertices = list([*vertices, vertices[0]])
    segments = [
        polygon_points[start : end + 1]
        for start, end in zip(vertices[:-1], vertices[1:])
    ]

    # Dispatch and reconstitute
    with ThreadPoolExecutor(max_workers) as tpe:
        reduced_segments = tpe.map(worker_wraps(epsilon), segments)

    return Polygon.merge(reduced_segments)


def vw_preserve(polygon_points: LineString, epsilon: float) -> LineString:
    """Visvalingam-Whyatt line reduction algorithm adapted to prevent crossings."""
    if len(polygon_points) < 3 or epsilon <= 0:
        return polygon_points

    max_points = len(polygon_points)

    tree = Rtree(data_stream(polygon_points.lines()))

    adjacent = [(i - 1, i + 1) for i in range(max_points)]

    pq = [
        VWScore(
            score=area,
            current=i + 1,
            left=i,
            right=i + 2,
        )
        for i, triangle in enumerate(polygon_points.triangles())
        if (area := triangle.signed_area()) >= 0
    ]
    heapq.heapify(pq)

    loss = 0
    while len(pq):
        smallest = heapq.heappop(pq)

        if smallest.score > epsilon:
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

        # Remove stale segments from R tree
        left_point = polygon_points[left]
        middle_point = polygon_points[smallest.current]
        right_point = polygon_points[right]

        line_1 = Line((left_point, middle_point))
        line_2 = Line((middle_point, right_point))
        tree.delete(ID, line_1.bbox())
        tree.delete(ID, line_2.bbox())

        # Reconnect vertices
        new_line = Line((left_point, right_point))
        tree.insert(ID, new_line.bbox(), new_line)

        # Update adjacent triangles
        recompute_triangles(polygon_points, pq, ll, left, right, rr, max_points)

        # Update loss
        loss += smallest.score

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
) -> None:
    choices = [(ll, left, right), (left, right, rr)]
    for ai, current_point, bi in choices:
        if not (0 <= ai < max and 0 <= bi < max):
            # Out of bounds
            continue

        area = Triangle((points[ai], points[current_point], points[bi])).signed_area()
        if area < 0:
            # Do not push negative areas
            continue

        v = VWScore(area, current_point, ai, bi)
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
