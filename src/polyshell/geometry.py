from collections import deque
from dataclasses import dataclass
from typing import Iterable, Iterator, Self, Sequence, overload


@dataclass(frozen=True)
class Coord:
    """A point in a 2-dimensional space."""

    coords: tuple[float, float]

    def __getitem__(self, index: int) -> float:
        return self.coords[index]

    def __add__(self, other: "Coord") -> "Coord":
        return Coord((self[0] + other[0], self[1] + other[1]))

    def __sub__(self, other: "Coord") -> "Coord":
        return Coord((self[0] - other[0], self[1] - other[1]))

    def __eq__(self, other: "Coord") -> bool:  # type: ignore
        return self.coords == other.coords

    def __iter__(self) -> Iterator[float]:
        return iter(self.coords)


@dataclass(frozen=True)
class Geometry:
    """A geometric object in a 2-dimensional space."""

    points: Iterable[Coord]

    def __iter__(self) -> Iterator[Coord]:
        return iter(self.points)

    def bbox(self) -> tuple[float, float, float, float]:
        x_coords, y_coords = zip(*self.points)
        return min(x_coords), min(y_coords), max(x_coords), max(y_coords)


@dataclass(frozen=True)
class Line(Geometry):
    """A line between two points in a 2-dimensional space."""

    points: tuple[Coord, Coord]

    def intersects(self, other: "Line") -> bool:
        """Check if two lines intersect at a unique point."""
        grad_self = self.points[1] - self.points[0]
        grad_other = other.points[1] - other.points[0]
        diff = other.points[0] - self.points[0]

        det = cross_2d(grad_self, grad_other)

        # Check for parallel lines
        if det == 0:
            return False

        # Find a candidate point
        lam = cross_2d(diff, grad_other) / det
        mu = cross_2d(diff, grad_self) / det

        # Check that candidate point is in bounds
        return (0 <= lam <= 1) and (0 <= mu <= 1)


@dataclass(frozen=True)
class Triangle(Geometry):
    """A data structure for triangles."""

    points: tuple[Coord, Coord, Coord]

    def signed_area(self) -> float:
        """Return the signed area of the triangle."""
        x, y, z = self.points
        return 0.5 * cross_2d(y - x, z - y)

    def unsigned_area(self) -> float:
        """Return the unsigned area of the triangle."""
        return abs(self.signed_area())


@dataclass
class LineString:
    """An ordered collection of points."""

    points: list[Coord]

    def __len__(self) -> int:
        return len(self.points)

    @overload
    def __getitem__(self, index: int) -> Coord: ...

    @overload
    def __getitem__(self, index: slice) -> "LineString": ...

    def __getitem__(self, index: int | slice):
        if isinstance(index, slice):
            return LineString(self.points[index])
        else:
            return self.points[index]

    def __iter__(self) -> Iterator[Coord]:
        return iter(self.points)

    def to_array(self) -> list[list[float]]:
        return list(map(list.__call__, self.points))

    @classmethod
    def from_array(cls, array: Sequence[tuple[float, float]]) -> Self:
        return cls(list(map(Coord.__call__, array)))

    def lines(self) -> Iterator[Line]:
        """Return an iterator of lines formed of adjacent points."""
        return map(Line.__call__, zip(self.points[:-1], self.points[1:]))

    def triangles(self) -> Iterator[Triangle]:
        """Return an iterator of triangles formed of three neighbouring points."""
        return map(
            Triangle.__call__,
            zip(*[self.points[i : i + len(self.points) - 2] for i in range(3)]),
        )

    @classmethod
    def merge(cls, line_strings: Iterable["LineString"]) -> Self:
        """Merge multiple connecting line strings."""
        line_strings = iter(line_strings)
        points = [*next(line_strings)]
        for line in line_strings:
            if line[0] != points[-1]:
                raise ValueError("Line segments do not connect.")
            points += line[1:]
        return cls(points)


class Polygon(LineString):
    """A polygon represented as a closed LineString."""

    def __post_init__(self):
        if self.points[0] != self.points[-1]:
            raise ValueError("Line string is not closed.")

    @overload
    def __getitem__(self, index: int) -> Coord: ...

    @overload
    def __getitem__(self, index: slice) -> "LineString": ...

    def __getitem__(self, index: int | slice):
        if isinstance(index, slice):
            if index.start <= index.stop:
                return LineString(self.points[index])
            else:
                return LineString(
                    self.points[index.start :: index.step]
                    + self.points[: index.stop : index.step]
                )
        else:
            return self.points[index]


def cross_2d(x: Coord, y: Coord) -> float:
    """Compute the two-dimensional cross product."""
    return x[0] * y[1] - x[1] * y[0]


def orientation(x: Coord, y: Coord, z: Coord) -> int:
    """Return the orientation for a triple of Coords."""
    cross = cross_2d(y - x, y - z)
    return int(cross > 0) - int(cross < 0)


def melkman(polygon: Polygon) -> Polygon:
    """Compute the convex hull of a Polygon using Melkman's algorithm."""
    if len(polygon) < 3:
        return polygon

    poly_iter = iter(polygon)
    x, y, z = [next(poly_iter) for _ in range(3)]
    hull = deque([z, x, y, z]) if orientation(x, y, z) > 0 else deque([z, y, x, z])

    while poly_iter:
        for v in poly_iter:
            if orientation(v, hull[0], hull[1]) > 0 or orientation(
                hull[-2], hull[-1], v
            ):
                break
        else:  # iterator is empty
            break

        while orientation(hull[-2], hull[-1], v) <= 0:
            hull.pop()
        hull.append(v)

        while orientation(v, hull[0], hull[1]) <= 0:
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
        deque([z, x, y, z])
        if orientation(x[1], y[1], z[1]) > 0
        else deque([z, y, x, z])
    )

    index = 2
    while poly_iter:
        for index, v in enumerate(poly_iter, start=index + 1):
            if (
                orientation(v, hull[0][1], hull[1][1]) < 0
                or orientation(hull[-2][1], hull[-1][1], v) < 0
            ):
                break
        else:  # iterator is empty
            break

        while orientation(hull[-2][1], hull[-1][1], v) <= 0:
            hull.pop()
        hull.append((index, v))

        while orientation(v, hull[0][1], hull[1][1]) <= 0:
            hull.popleft()
        hull.appendleft((index, v))

    return [index for index, _ in hull]
