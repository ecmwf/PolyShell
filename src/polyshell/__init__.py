import numpy as np
import numpy.ma as ma

from polyshell.heap import PriorityQueue


def reduce_polygon(polygon_points: list, tol: float = 1e-2) -> np.ndarray:
    """Reduce a polygon while retaining coverage."""
    polygon_points = ma.masked_array(
        polygon_points, mask=np.zeros_like(polygon_points, dtype=bool)
    )

    # Store areas using an indexed priority queue
    areas = np.array([-np.inf, *get_areas(polygon_points), -np.inf])

    pq = PriorityQueue()
    for index, area in enumerate(areas):
        if area > 0:
            pq.push(index, area)

    loss = 0.0
    while loss < tol:
        # Find minimum
        index, area = pq.pop()
        loss += area

        # Update mask
        polygon_points[index] = ma.masked
        mask = polygon_points.mask[:, 0]

        # Update areas
        before = find_last(mask, index)
        after = find_next(mask, index)

        if before != 0:
            two_before = find_last(mask, before)
            new_area = get_areas(polygon_points[[two_before, before, after]])[0]

            if new_area > 0:
                pq.push(before, new_area)
            elif before in pq:
                pq.remove(before)

        if after != len(polygon_points) - 1:
            two_after = find_next(mask, after)
            new_area = get_areas(polygon_points[[before, after, two_after]])[0]

            if new_area > 0:
                pq.push(after, new_area)
            elif after in pq:
                pq.remove(after)

    return polygon_points[~mask]


def get_areas(points: np.ndarray) -> np.ndarray:
    """Find the signed area of each triangle."""
    x, y, z = points[:-2], points[1:-1], points[2:]
    return 0.5 * np.cross(y - x, z - y, axis=-1)


def find_next(arr: list, index: int) -> int:
    for i, x in enumerate(arr[index + 1 :], start=1):
        if not x:
            return index + i
    else:
        raise ValueError("No value found.")


def find_last(arr: list, index: int) -> int:
    return -(find_next(arr[::-1], index=-(index + 1)) + 1)
