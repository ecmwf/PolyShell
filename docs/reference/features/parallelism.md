# Acceleration Through Parallelism

Both [RDP](../algorithms/ramer-douglas-peucker.md) and [Charshape](../algorithms/charshape.md) take a bottom-up approach, starting with the
convex hull and progressively introducing detail, they can be readily parallelized. For Charshape, as an edge is
removed, two more are uncovered. Likewise with RDP, a segment is split in two. In both instances, a task is split into
two sub-tasks in a divide-and-conquer approach. As a result, both Charshape and RDP are ideal candidates for parallelism
through [work stealing](https://en.wikipedia.org/wiki/Work_stealing).

While this approach is attractive, reduction occurs out-of-order, making it challenging to reduce to a fixed length or
for adaptive algorithms, each of which require global observability.

Thus far, benchmarking has shown that work stealing yields only modest gains in performance. This mainly due to
overheads in the Python bindings and preprocessing steps which cannot be performed in parallel. For this reason,
PolyShell does not currently implement these parallelisation strategies for either algorithm. If significant performance
gains are made in either area, then multi-core reduction will become a priority.
