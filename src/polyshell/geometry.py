"""Geometry classes for PolyShell."""

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

    def cross_2d(self: "Coord", other: "Coord") -> float:
        """Compute the two-dimensional cross product."""
        return self[0] * other[1] - self[1] * other[0]

    def orientation(self: "Coord", y: "Coord", z: "Coord") -> int:
        """Return the orientation for a triple of Coords."""
        cross = (y - self).cross_2d(y - z)
        return int(cross > 0) - int(cross < 0)


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

        det = grad_self.cross_2d(grad_other)

        # Check for parallel lines
        if det == 0:
            return False

        # Find a candidate point
        lam = diff.cross_2d(grad_other) / det
        mu = diff.cross_2d(grad_self) / det

        # Check that candidate point is in bounds
        return (0 <= lam <= 1) and (0 <= mu <= 1)


@dataclass(frozen=True)
class Triangle(Geometry):
    """A data structure for triangles."""

    points: tuple[Coord, Coord, Coord]

    def signed_area(self) -> float:
        """Return the signed area of the triangle."""
        x, y, z = self.points
        return 0.5 * (y - x).cross_2d(z - y)

    def unsigned_area(self) -> float:
        """Return the unsigned are of the triangle."""
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


@dataclass
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
