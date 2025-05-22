"""A simple KDTree wrapper for queries on triangles."""

import numpy as np
from scipy.spatial import KDTree

from polyshell.utils import cross_2d


class DynPointTree:
    """A dynamic kd-tree with queries for rectangles and triangles."""

    def __init__(self, points: np.ndarray):
        """Initialize the kd-tree tree."""
        if not isinstance(points, np.ma.MaskedArray):
            points = np.ma.masked_array(points)

        self.points = points
        self.kd_tree = KDTree(points.data)

    def query_rectangle(self, bbox: np.ndarray) -> np.ndarray:
        """Locate all points which lie inside a bounding box."""
        # Query the KD-Tree with a ball which inscribes the bounding box
        center = np.mean(bbox, axis=0)
        max_distance = np.max(np.diff(bbox, axis=0)) / 2
        candidate_indices = self.kd_tree.query_ball_point(center, max_distance)
        candidate_points = self.points[candidate_indices]

        # Filter candidates by the bounding box and mask
        valid_points = np.array(
            [
                point
                for point in candidate_points
                if not np.ma.is_masked(point) and self.is_point_in_bbox(point, bbox)
            ]
        )

        return valid_points

    def check_rectange(self, bbox: np.ndarray) -> bool:
        """Check if any points lie inside a bounding box."""
        return len(self.query_rectangle(bbox)) > 0

    def query_triangle(self, triangle: np.ndarray) -> np.ndarray:
        """Locate all points which lie inside a triangle."""
        # Query points within the bounding box
        bbox = self.get_bbox(triangle)
        candidate_points = self.query_rectangle(bbox)

        # Iterate over candidate points
        return np.array(
            [
                point
                for point in candidate_points
                if self.is_point_in_triangle(point, triangle)
            ]
        )

    def check_triangle(self, triangle: np.ndarray) -> bool:
        """Check if any points lie inside a triangle."""
        return len(self.query_triangle(triangle)) > 0

    @staticmethod
    def get_bbox(points: np.ndarray) -> np.ndarray:
        """Get the bounding box of a point cloud."""
        return np.array([np.min(points, axis=0), np.max(points, axis=0)])

    @staticmethod
    def is_point_in_bbox(p: np.ndarray, bbox: np.ndarray) -> bool:
        """Check if a point p is in the interior of a bounding box."""
        min, max = bbox
        return (min < p).all() and (p < max).all()

    @staticmethod
    def is_point_in_triangle(p: np.ndarray, triangle: np.ndarray) -> bool:
        """Check if a point p is in the interior of the given triangle."""
        a, b, c = triangle

        x = cross_2d(b - a, p - a)
        y = cross_2d(c - b, p - b)
        z = cross_2d(a - c, p - c)

        return all(cross > 0 for cross in (x, y, z)) or all(
            cross < 0 for cross in (x, y, z)
        )
