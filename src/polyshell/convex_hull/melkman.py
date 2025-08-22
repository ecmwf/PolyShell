"""Melkman's algorithm to compute the convex hull of a simple polygon."""

from collections import deque

from polyshell.geometry import Polygon


def melkman(polygon: Polygon) -> Polygon:
    """Compute the convex hull of a Polygon using Melkman's algorithm."""
    if len(polygon) < 3:
        return polygon

    poly_iter = iter(polygon)
    x, y, z = [next(poly_iter) for _ in range(3)]
    hull = deque([z, x, y, z]) if x.orientation(y, z) > 0 else deque([z, y, x, z])

    while poly_iter:
        for v in poly_iter:
            if (
                v.orientation(hull[0], hull[1]) < 0
                or hull[-2].orientation(hull[-1], v) < 0
            ):
                break
        else:  # iterator is empty
            break

        while hull[-2].orientation(hull[-1], v) <= 0:
            hull.pop()
        hull.append(v)

        while v.orientation(hull[0], hull[1]) <= 0:
            hull.popleft()
        hull.appendleft(v)

    return Polygon(list(hull))


def melkman_indices(polygon: Polygon) -> list[int]:
    """Compute the indices of the convex hull using Melkman's algorithm."""
    if len(polygon) < 3:
        return list(range(len(polygon)))

    poly_iter = iter(polygon)
    x, y, z = [(i, next(poly_iter)) for i in range(3)]
    hull = (
        deque([z, x, y, z]) if x[1].orientation(y[1], z[1]) > 0 else deque([z, y, x, z])
    )

    index = 2
    while poly_iter:
        for index, v in enumerate(poly_iter, start=index + 1):
            if (
                v.orientation(hull[0][1], hull[1][1]) < 0
                or hull[-2][1].orientation(hull[-1][1], v) < 0
            ):
                break
        else:  # iterator is empty
            break

        while hull[-2][1].orientation(hull[-1][1], v) <= 0:
            hull.pop()
        hull.append((index, v))

        while v.orientation(hull[0][1], hull[1][1]) <= 0:
            hull.popleft()
        hull.appendleft((index, v))

    return [index for index, _ in hull]
