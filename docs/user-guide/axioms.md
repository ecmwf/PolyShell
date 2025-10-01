# PolyShell's Axioms

PolyShell promises to provide reliable high-performance polygon reduction algorithms which behave in a predictable way.
PolyShell's axioms consist of both the assumptions we make about a user's input and, given these are upheld, the
assumptions the user can make about the output they receive.

---

## Polygon Validity

All input to PolyShell is expected to be valid.

!!! abstract "Definition"

    A polygon is said to be valid if:

    1. It consists of either zero or at least three unique points.
    2. It is closed.
    3. There are no duplicate points or self-intersections.
    4. The vertices are stored as a sequence in clockwise order.

Whether a polygon abides to these requirements can be checked using the provided `is_valid` function.

!!! tip

    When using validated functions, PolyShell with automatically correct for incorrect ordering. This point is only
    relevant for users who wish to use the unchecked algorithms.

---

## Our Promise

Provided the assumptions made above are upheld, PolyShell makes the following promises:

1. The reduced polygon will always be [valid](#polygon-validity).
2. The reduced polygon will always contain the input polygon in its interior.
3. Vertices are never moved nor added.
4. Reduction preserves the ordering of the vertices, up to shifts and reversal.
