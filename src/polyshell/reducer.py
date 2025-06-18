import heapq
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
    intersector: bool

    def __post_init__(self):
        self.sort_index = self.score


def data_stream(geoms: Iterable[Geometry]):
    for item in geoms:
        yield (ID, item.bbox(), item)


def reduce_polygon(polygon_points: Polygon, epsilon: float) -> Polygon:
    """Reduce a polygon while retaining coverage."""
    tree = Rtree(data_stream(polygon_points.lines()))

    # Slice, dispatch, and reconstitute
    vertices = ConvexHull(polygon_points.to_array()).vertices[::-1]
    vertices = list([*vertices, vertices[0]])

    reduced_poly = Polygon.merge(
        [
            vw_preserve(polygon_points[start : end + 1], epsilon, tree)
            for start, end in zip(vertices[:-1], vertices[1:])
        ]
    )

    return reduced_poly


def vw_preserve(polygon_points: LineString, epsilon: float, tree: Rtree) -> LineString:
    """Visvalingam-Whyatt line reduction algorithm adapted to prevent crossings."""
    if len(polygon_points) < 3 or epsilon <= 0:
        return polygon_points

    max_points = len(polygon_points)

    adjacent = [(i - 1, i + 1) for i in range(len(polygon_points))]

    pq = [
        VWScore(
            score=triangle.unsigned_area(),
            current=i + 1,
            left=i,
            right=i + 2,
            intersector=False,
        )
        for i, triangle in enumerate(polygon_points.triangles())
    ]
    heapq.heapify(pq)

    while len(pq):
        smallest = heapq.heappop(pq)

        if smallest.score > epsilon:
            break

        # Check if the score is invalidated
        left, right = adjacent[smallest.current]
        if left != smallest.left or right != smallest.right:
            continue

        # Check for self-intersection
        smallest.intersector = tree_intersect(tree, smallest, polygon_points)

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
        recompute_triangles(
            smallest, polygon_points, pq, ll, left, right, rr, max_points, epsilon
        )

    # Filter out any deleted points
    return LineString(
        [point for point, adj in zip(polygon_points, adjacent) if adj != (0, 0)]
    )


def recompute_triangles(
    smallest: VWScore,
    points: LineString,
    pq: list[VWScore],
    ll: int,
    left: int,
    right: int,
    rr: int,
    max: int,
    epsilon: float,
) -> None:
    choices = [(ll, left, right), (left, right, rr)]
    for ai, current_point, bi in choices:
        if not (0 <= ai < max and 0 <= bi < max):
            # Out of bounds
            continue

        area = Triangle((points[ai], points[current_point], points[bi])).unsigned_area()

        if smallest.intersector and current_point < smallest.current:
            area = -epsilon

        v = VWScore(area, current_point, ai, bi, intersector=False)
        heapq.heappush(pq, v)


def tree_intersect(tree: Rtree, triangle: VWScore, points: LineString) -> bool:
    """Check if removal of a triangle causes a self-intersection."""
    new_segment_start = points[triangle.left]
    new_segment_end = points[triangle.right]

    new_segment = Line((new_segment_start, new_segment_end))

    bounding_rect = Triangle(
        (points[triangle.left], points[triangle.current], points[triangle.right])
    ).bbox()

    for candidate_item in tree.intersection(bounding_rect, objects=True):
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
