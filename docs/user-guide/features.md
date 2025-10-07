# Features

PolyShell currently provides three reduction algorithms to fit your needs. Each varies in their performance and
reduction characteristics.

| Algorithm                                       | Available modes | Parallelism             | Fastest for      | Characteristics                                  |
|-------------------------------------------------|-----------------|-------------------------|------------------|--------------------------------------------------|
| [Visvalingam-Whyatt](#visvalingam-whyatt)       | epsilon, length | :octicons-check-16:[^1] | Small reductions | Smoothes boundary roughness, minimises area gain |
| [Ramer-Douglas-Peucher](#ramer-douglas-peucker) | epsilon         | :octicons-check-16:     | Large reductions | Retains sharp concavities                        |
| [Charshape](#charshape)                         | epsilon, length | :octicons-x-16:         | Large reductions | Minimises edge length                            |

[^1]: Parallelism is currently only supported by the epsilon reduction mode.

!!! tip

    Whenever possible PolyShell will reduce a single polygon across multiple cores. This is handled
    automatically and can lead to a sizable uplift in performance.

---

## Algorithms

!!! note

    If no reduction method is specified, PolyShell will default to [Visvalingam-Whyatt](#visvalingam-whyatt).

### Visvalingam-Whyatt

The Visvalingam-Whyatt algorithm iteratively removed vertices based on the area of the triangle formed with its two
neighbours. At each iteration a vertex is removed only if the area of the polygon increases and that its topology is
preserved.

For more information on the algorithm see the [reference](../reference/algorithms/visvalingam-whyatt.md).

### Ramer-Douglas-Peucker

The Ramer-Douglas-Peucker algorithm recursively splits the polygon into segments. At each step of the recursion, a chord
is drawn between endpoints of the current segment, and the segment is split at furthest visible point from this chord.
Once this distance becomes small, the segment is reduced to a single chord.

For more information on the algorithm see the [reference](../reference/algorithms/ramer-douglas-peucker.md).

### Charshape

The Charshape algorithm iteratively adds vertices to minimise the maximum edge length. It begins by computing the
[constrained Delaunay triangulation](https://en.wikipedia.org/wiki/Constrained_Delaunay_triangulation), starting with
the convex hull, iteratively adding edges.

For more information on the algorithm see the [reference](../reference/algorithms/charshape.md).

---

## Running Modes

### Epsilon

_Reduces a polygon to a set resolution._

The precise meaning of epsilon varies depending on the particular algorithm, but broadly related to the resolution
of a polygon.

It is always the case that a smaller value of epsilon will lead to a more detailed approximation, at the expense of a
greater number of vertices.

| Algorithm                                       | Units  | Definition                                                                                                |
|-------------------------------------------------|--------|-----------------------------------------------------------------------------------------------------------|
| [Visvalingam-Whyatt](#visvalingam-whyatt)       | Area   | The minimum area of the smallest triangle formed by a triple of connected vertices                        |
| [Ramer-Douglas-Peucher](#ramer-douglas-peucker) | Length | The maximum distance between a string of vertices and the chord which connects the first and final points |
| [Charshape](#charshape)                         | Length | The maximum line segment length along the boundary, provided a string of shorter segments exists          |

Epsilon reduction mode can be enabled for supported algorithms using the `reduction_mode` argument, providing tolerance
in the third position or using the keyword argument `epsilon`:

=== "Python 3.10+"

    ```python
    from polyshell import reduce_polygon

    original = [
        (0.0, 0.0),
        (0.0, 1.0),
        (0.5, 0.5),
        (1.0, 1.0),
        (1.0, 0.0),
        (0.0, 0.0),
    ]

    reduced = reduce_polygon(original, "epsilon", epsilon=0.1, method="vw")
    ```

### Length

_Reduces a polygon to a target length._

Depending on reduction direction the length is interpreted as a minimum or maximum. Provided the target length is
between the size of the original polygon and the convex hull, the target is guaranteed to be obtained.

Length reduction mode can be enabled for supported algorithms using the `reduction_mode` argument, providing the desired
length in the third position or using the keyword argument `length`:

=== "Python 3.10+"

    ```python
    from polyshell import reduce_polygon

    original = [
        (0.0, 0.0),
        (0.0, 1.0),
        (0.5, 0.5),
        (1.0, 1.0),
        (1.0, 0.0),
        (0.0, 0.0),
    ]

    # Length is the size of the coordinate vector, not the number of unique points
    reduced = reduce_polygon(original, "length", length=5, method="charshape")
    assert len(reduced) == 5
    ```

---

## External Package Support

PolyShell currently supports polygons stored using [Shapely's Polygon class](https://shapely.readthedocs.io/en/stable/)
and also as a [NumPy ndarray](https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html) of coordinate pairs.
In each case, the reduced polygon will be returned as a list of
coordinate pairs.
