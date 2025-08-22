"""Ramer–Douglas–Peucker line reduction algorithm."""

from polyshell.geometry import (
    Geometry,
    Line,
    LineString,
    Triangle,
)

from ..vw.vw import VWScore, VWLineString, data_stream

from .loss_funcs import LossFunction

ID = 0  # ID for rtree


class RDPLineString(VWLineString):
    def __init__(self, orig: LineString, loss_fn: LossFunction):
        super().__init__(orig, loss_fn)

    def reduce(self, epsilon: float, min_len: int, start: int = 0, end: int = None) -> None:

        end = end or self.len
        if end - start < 3 or self.len <= min_len:
            return

        tmp_ls = LineString.from_array(self.orig[start:end])
        drop, keep = [], []

        # Find the point farthest from the [start, end] line
        max_score = -1.0
        max_score_keep = -1.0
        index = start + 1
        index_keep = start + 1
        for i, triangle in enumerate(tmp_ls.triangles2()):
            idx = start + i + 1
            score = self.loss_fn(triangle)
            (keep if score >= 0 else drop).append(idx)

            if score > max_score_keep:
                index_keep, max_score_keep = idx, score

            if abs(score) > max_score:
                index, max_score = idx, abs(score)

        candidates = [start] + keep + [end - 1]

        if max_score <= epsilon:

            if len(keep) > 1 or self.tree_intersect_segment(
                    LineString([self.orig[c] for c in candidates])):
                # Keep the current point even though could be < epsilon, recurse on both segments
                self.reduce(epsilon=epsilon, min_len=min_len, start=start, end=index_keep + 1)
                self.reduce(epsilon=epsilon, min_len=min_len, start=index_keep, end=end)
                return

            for d in drop:
                left, right = self.adjacent[d]
                # Update adjacency list
                ll, _ = self.adjacent[left]
                _, rr = self.adjacent[right]
                self.adjacent[left] = (ll, right)
                self.adjacent[right] = (left, rr)
                self.adjacent[d] = (0, 0)

                # Reconnect vertices
                left_point = self.orig[left]
                right_point = self.orig[right]
                new_line = Line((left_point, right_point))
                self.tree.insert(ID, new_line.bbox(), new_line)

                # Update loss
                # self.loss += score
                self.len -= 1

            return

        # Keep the farthest point, recurse on both segments
        self.reduce(epsilon=epsilon, min_len=min_len, start=start, end=index + 1)
        self.reduce(epsilon=epsilon, min_len=min_len, start=index, end=end)


    def tree_intersect_segment(self, points: LineString) -> bool:
        """
        Returns True if any segment in the given LineString - ``points``
        intersects an existing segment in the R-tree.
        """
        # Iterate over each consecutive pair in points
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            seg = Line((p1, p2))
            bbox = seg.bbox()

            # Query all indexed segments whose bbox overlaps this segment
            for item in self.tree.intersection(bbox, objects=True):
                other: Line = item.object  # type: ignore
                o0, o1 = map(tuple, other)

                # Skip if they share an endpoint
                if {o0, o1} & {tuple(p1), tuple(p2)}:
                    continue

                if seg.intersects(other):
                    return True

        # No crossings found across all segments
        return False
