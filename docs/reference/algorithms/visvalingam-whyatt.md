# Visvalingam-Whyatt

The Visvalingam-Whyatt reduction method provided by PolyShell consists of a few modifications to the original line
reduction algorithm by Visvalingam and Whyatt[^1] in order to guarantee [PolyShell's axioms].

[^1]: [M. Visvalingam, J. D. Whyatt, 2013. Line generalisation by repeated elimination of points.](https://doi.org/10.1179/000870493786962263)

## Visvalingam-Whyatt Algorithm

In the original algorithm, vertices are assigned scores as measures of a point's importance, based upon the triangle formed by a vertex with its
two neighbours. In the original algorithm this score is taken to be area displacement (AD), defined as the unsigned area
of the associated triangle. Modifications to Visvalingam's algorithm by other scoring metrics have also been
investigated[^2], leading to Visvalingam coining the term "effective area" (EA) to describe the score of a vertex more
generally. Such examples include the introduction of the factor $EA = AD (1 - \cos{\theta})$ used by
[Mapshaper](https://github.com/mbloch/mapshaper) to provide additional smoothing[^3]. The algorithm then proceeds by
removing vertices in order of their score, from lowest to highest, until the score of a vertex exceeds some threshold.

[^2]: [M. Visvalingam, 2016. The Visvalingam Algorithm: Metrics, Measures and Heuristics.](https://doi.org/10.1080/00087041.2016.1151097)

[^3]: [M. Bloch, 2014. Some weighting functions for Visvalingam simplification.](https://gist.github.com/mbloch/5505b92642f6e0361037)

---

## Modifications

To apply the Visvalingam-Whyatt algorithm to the problem of polygon reduction, it is necessary to correct for possible
self-intersections which may occur. These issues tend to occur most frequently in channel-like geometries, like the
example given below. One fairly common solution is to check that removal of a vertex will not lead to a
self-intersection, otherwise it is skipped. Naive implementations can prove costly, however this can be somewhat
improved by first querying an [R-tree](https://en.wikipedia.org/wiki/R-tree) to reduce the number of likely culprits.

TODO: Img with caption explanation

Once the algorithm has been extended to the reduction of polygons, ensuring coverage is a relatively simple process.
When assigning scores, if removal of a vertex would lead to a loss in coverage, the effective area is said to be
infinite, otherwise it is set according to any valid metric. Thus, at each iteration, vertices removed are guaranteed
to increase the area of the reduced polygon and hence ensure coverage at each step.

---

## Implementation Notes

The formulation of [PolyShell's axioms] provides the opportunity for some additional performance improvements beyond
those possible when using the standard Visvalingam-Whyatt algorithm. In this section we will describe all the
adjustments made beyond a typical implementation of the Visvalingam-Whyatt algorithm. We will also provide some
justification as to why these reductions are valid and some expectations on the resulting uplift in performance.

### Pre-processing

Immediately obvious is that the minimal reduction of any polygon is it's [convex hull](https://en.wikipedia.org/wiki/Convex_hull).
For most purposes this is a poor reduction, losing almost all detail in the original shape. The convex hull does however
identify which vertices are invariant under reduction. This feature allows us to segment the polygon into isolated
sections, each of which can be reduced independently of the others, allowing for parallel reduction on a single polygon.
For this purpose we use Melkman's algorithm, to compute the convex hull in linear time[^4].

[^4]: [A. Melkman, 1987. On-line construction of the convex hull of a simple polyline.](https://doi.org/10.1016/0020-0190(87)90086-X)

### R-tree Adjustments

Adaptations of Visvalingam-Whyatt for polygon reduction require use of an R-tree to prevent self-intersections. For
typical reduction algorithms, this requires edges to be removed from the tree and new edges inserted at each iteration.
In PolyShell's implementation, both of these steps are skipped while retaining correctness. Deletion is no longer
necessary, as our reduction only expands outwards. Hence, edges which are removed can never cause self-intersections.
Similarly, no new edges need to be added, as if a reduction causes an intersection with a new edge, then it would have
already caused an intersection with one of the original edges. We have found that while a larger tree must be queried
at every iteration, the savings by not rebalancing the tree outweigh any potential cost.

[PolyShell's axioms]: ../../user-guide/axioms.md
