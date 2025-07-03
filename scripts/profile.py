"""Run a profiler on a test polygon."""

import pickle

import numpy as np

from polyshell import reduce_polygon
from polyshell.geometry import Coord, Polygon

import pyinstrument

if __name__ == "__main__":
    with open("./tests/data/ionian_polygon_points.pkl", "rb") as f:
        original_polygon = np.array(pickle.load(f))

    original_polygon = Polygon([Coord(tuple(point)) for point in original_polygon])  # type: ignore
    with pyinstrument.profile():
        reduced_polygon = reduce_polygon(original_polygon, epsilon=1e-6)
