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
        yield ID, item.bbox(), item


def worker_wraps(epsilon: float):
    def worker(ls: LineString) -> LineString:
        tree = Rtree(data_stream(ls.lines()))
        return dp_preserve(ls, epsilon, tree)

    return worker


def reduce_polygon(
    polygon: Polygon, epsilon: float, max_workers: int | None = None
) -> Polygon:
    """Reduce a polygon while retaining coverage."""
    # Slice into LineStrings
    vertices = ConvexHull(polygon.to_array()).vertices[::-1]
    vertices = list([*vertices, vertices[0]])
    segments = [
        polygon[start: end + 1]
        for start, end in zip(vertices[:-1], vertices[1:])
    ]

    # Dispatch and reconstitute
    with ThreadPoolExecutor(max_workers) as tpe:
        reduced_segments = tpe.map(worker_wraps(epsilon), segments)

    return Polygon.merge(reduced_segments)


def reduce_losses(polygon: Polygon, max_workers: int | None = None) -> list[list[float]]:
    # Slice into LineStrings
    vertices = ConvexHull(polygon.to_array()).vertices[::-1]
    vertices = list([*vertices, vertices[0]])
    segments = [
        polygon[start: end + 1]
        for start, end in zip(vertices[:-1], vertices[1:])
    ]

    # Dispatch and reconstitute
    with ThreadPoolExecutor(max_workers) as tpe:
        reduced_segments = tpe.map(vw_indices, segments)

    return [[vw_score.score for vw_score in removal_order] for removal_order in reduced_segments]


def reduce_losses_dp(polygon: Polygon, max_workers: int | None = None) -> list[list[float]]:
    # Slice into LineStrings
    vertices = ConvexHull(polygon.to_array()).vertices[::-1]
    vertices = list([*vertices, vertices[0]])
    segments = [
        polygon[start: end + 1]
        for start, end in zip(vertices[:-1], vertices[1:])
    ]

    trees = [
        Rtree(data_stream(segment.lines()))
        for segment in segments
    ]

    # Dispatch and reconstitute
    with ThreadPoolExecutor(max_workers) as tpe:
        reduced_segments = tpe.map(dp_indices, segments, trees)

    return [scores for _, scores in reduced_segments]


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

        # Reconnect vertices
        left_point = polygon_points[left]
        right_point = polygon_points[right]
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


def vw_indices(polygon_points: LineString) -> list[VWScore]:
    """Removal order from the Visvalingam-Whyatt line reduction algorithm."""
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

    removal_order = []
    while len(pq):
        smallest = heapq.heappop(pq)

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

        # Reconnect vertices
        left_point = polygon_points[left]
        right_point = polygon_points[right]
        new_line = Line((left_point, right_point))
        tree.insert(ID, new_line.bbox(), new_line)

        # Update adjacent triangles
        recompute_triangles(polygon_points, pq, ll, left, right, rr, max_points)

        # Update ordering
        removal_order.append(smallest)

    return removal_order


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


"""Functions for the Ramer–Douglas–Peucker algorithm."""


def tree_intersect_segment(tree: Rtree, points: LineString) -> bool:
    """
    Return True if any segment in the given LineString ``points``
    intersects an existing segment in the R-tree ``tree``.
    """
    # Iterate over each consecutive pair in points
    for i in range(len(points) - 1):
        start, end = points[i], points[i + 1]
        seg = Line((start, end))
        bbox = seg.bbox()

        # Query all indexed segments whose bbox overlaps this segment
        for item in tree.intersection(bbox, objects=True):
            other: Line = item.object  # type: ignore
            o0, o1 = map(tuple, other)

            # Skip if they share an endpoint
            if {o0, o1} & {tuple(start), tuple(end)}:
                continue

            if seg.intersects(other):
                return True

    # No crossings found across all segments
    return False


def dp_preserve(
    polygon_points: LineString, epsilon: float, tree: Rtree
) -> LineString:
    """
    Recursively apply Douglas–Peucker: keep endpoints, find point with max
    area to baseline; if area > epsilon, split and recurse, else drop intermediates.
    """
    if len(polygon_points) < 3 or epsilon <= 0:
        return polygon_points

    start, end = polygon_points[0], polygon_points[-1]
    intermediate = []

    # Find the point farthest from the [start, end] line
    max_area = 0.0
    index = 0
    for i in range(1, len(polygon_points) - 1):
        # Compute area formed by intermediate points with the end points line segment
        a = Triangle((start, end, polygon_points[i])).signed_area()
        if a > 0:
            intermediate.append(polygon_points[i])
        if abs(a) > max_area:
            index, max_area = i, abs(a)

    candidates = [start] + intermediate + [end]

    if tree_intersect_segment(tree, LineString(candidates)):
        # Keep the current point even though could be < epsilon, recurse on both segments
        left = dp_preserve(polygon_points[: index + 1], epsilon, tree)
        right = dp_preserve(polygon_points[index:], epsilon, tree)
        return LineString.merge([left, right])
    else:
        if max_area <= epsilon:
            # All intermediate points are within epsilon: collapse to just [start, end]
            # return LineString([start, end])
            # Fall back to polygon_points to ensure no self-intersections
            # return polygon_points
            # Collapse to [start, inter, end] only if no line segment crossings,
            # where inter are points with +ve areas to ensure coverage
            new_lines = [Line((candidates[point], candidates[point + 1])) for point in range(len(candidates) - 1)]
            for new_line in new_lines:
                tree.insert(ID, new_line.bbox(), new_line)
            return LineString(candidates)
        else:
            # Keep the farthest point, recurse on both segments
            left = dp_preserve(polygon_points[: index + 1], epsilon, tree)
            right = dp_preserve(polygon_points[index:], epsilon, tree)

            return LineString.merge([left, right])


def dp_indices(
    polygon_points: LineString, tree: Rtree
) -> {LineString, list[float]}:
    """
    Removal order for the Douglas–Peucker algorithm.
    """
    if len(polygon_points) < 3:
        return polygon_points, []

    start, end = polygon_points[0], polygon_points[-1]
    intermediate = []
    removal_order = []

    # Find the point farthest from the [start, end] line
    max_area = 0.0
    index = 0
    for i in range(1, len(polygon_points) - 1):
        # Compute area formed by intermediate points with the end points line segment
        a = Triangle((start, end, polygon_points[i])).signed_area()
        if a > 0:
            intermediate.append(polygon_points[i])
        else:
            removal_order.append(Triangle((polygon_points[i - 1], polygon_points[i], polygon_points[i + 1])).unsigned_area())
        if abs(a) > max_area:
            index, max_area = i, abs(a)

    candidates = [start] + intermediate + [end]

    if tree_intersect_segment(tree, LineString(candidates)):
        # Keep the current point even though could be < epsilon, recurse on both segments
        left, ro_left = dp_indices(polygon_points[: index + 1], tree)
        right, ro_right = dp_indices(polygon_points[index:], tree)
        return LineString.merge([left, right]), ro_left + ro_right
    else:
        if max_area <= 100.:
            # Collapse to [start, inter, end] only if no line segment crossings,
            # where inter are points with +ve areas to ensure coverage
            new_lines = [Line((candidates[point], candidates[point + 1])) for point in range(len(candidates) - 1)]
            for new_line in new_lines:
                tree.insert(ID, new_line.bbox(), new_line)
            return LineString(candidates), removal_order
        else:
            # Keep the farthest point, recurse on both segments
            left, ro_left = dp_indices(polygon_points[: index + 1], tree)
            right, ro_right = dp_indices(polygon_points[index:], tree)

            return LineString.merge([left, right]), ro_left + ro_right

