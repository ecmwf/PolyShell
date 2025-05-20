import numpy as np

from polyshell.heap import PriorityQueue
from polyshell.kd_tree import DynPointTree
from polyshell.utils import cross_2d


def reduce_polygon(polygon_points: list, tol: float = 1e-2) -> np.ndarray:
    """Reduce a polygon while retaining coverage."""
    polygon_points = np.ma.masked_array(
        polygon_points, mask=np.zeros_like(polygon_points, dtype=bool)
    )

    # Populate kd-tree for fast intersection tests
    point_tree = DynPointTree(polygon_points)

    # Pre-compute areas and populate a priority queue
    areas = np.array([-np.inf, *get_areas(polygon_points), -np.inf])
    area_queue = PriorityQueue()
    for index, area in enumerate(areas):
        if area > 0:
            area_queue.push(index, area)

    # Iterate
    loss = 0.0
    while loss < tol:
        # Find minimum
        index, area = area_queue.pop()

        # Find adjacent points
        mask = polygon_points.mask[:, 0]
        before = find_last(mask, index)
        after = find_next(mask, index)
        triangle = polygon_points[[before, index, after]]

        # Verify no crossing occurs
        if point_tree.check_triangle(triangle):
            continue

        # Update mask
        polygon_points[index] = np.ma.masked
        loss += area

        # Update areas
        if before != 0:
            two_before = find_last(mask, before)
            new_area = get_areas(polygon_points[[two_before, before, after]])[0]

            if new_area > 0:
                area_queue.push(before, new_area)
            elif before in area_queue:
                area_queue.remove(before)

        if after != len(polygon_points) - 1:
            two_after = find_next(mask, after)
            new_area = get_areas(polygon_points[[before, after, two_after]])[0]

            if new_area > 0:
                area_queue.push(after, new_area)
            elif after in area_queue:
                area_queue.remove(after)

    return polygon_points[~polygon_points.mask[:, 0]]


def get_areas(points: np.ndarray) -> np.ndarray:
    """Find the signed area of each triangle."""
    x, y, z = points[:-2], points[1:-1], points[2:]
    return 0.5 * cross_2d(y - x, z - y)


def find_next(arr: list, index: int) -> int:  # TODO: Replace with searchsorted
    for i, x in enumerate(arr[index + 1 :], start=1):
        if not x:
            return index + i
    else:
        raise ValueError("No value found.")


def find_last(arr: list, index: int) -> int:
    return -(find_next(arr[::-1], -(index + 1)) + 1)
