# PolyShell's Axioms

PolyShell promises to provide reliable high-performance polygon reduction algorithms which behave in a predictable way.
PolyShell's axioms consist of both the assumptions we make about a user's input and, given these are upheld, the
assumptions the user can make about the output they receive.

!!! warning

    PolyShell provides little-to-no input validation. While memory-safety is always guaranteed, if the following
    assumptions are broken you may receive an error or an invalid reduction. If you are uncertain whether your data upholds
    these requirements, we encourage you to use [Shapely](https://shapely.readthedocs.io/en/stable/) to perform your own
    validation first.

---

## Polygon Validity

All input to PolyShell is expected to be valid.

!!! abstract "Definition"

    A polygon is said to be valid if:

    1. It is a [simple polygon].
    2. The vertices are stored as a sequence in clockwise order.
    3. The first and last coordinate in the sequence are equal.

[simple polygon]: https://en.wikipedia.org/wiki/Simple_polygon, "A polygon with no holes or self-intersections."

---

## Our Promise

Provided the assumptions made above are upheld, PolyShell makes the following promises:

1. The reduced polygon will always be [valid](#polygon-validity).
2. The reduced polygon will always contain the input polygon in its interior.
3. Vertices are never moved nor added.
4. Reduction preserves the ordering of the vertices, but is not necessarily stable.

!!! note

    While the sequence of vertices within the polygon is preserved, the location of the first vertex may shift depending on
    the algorithm used.
