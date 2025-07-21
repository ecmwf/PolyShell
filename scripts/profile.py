"""Run a profiler on a test polygon."""

import pickle

import numpy as np
import pyinstrument

from polyshell import reduce_polygon
from polyshell.geometry import Coord, Polygon

if __name__ == "__main__":
    with open("./tests/data/sea/ionian_sea.pkl", "rb") as f:
        original_polygon = np.array(pickle.load(f))

    original_polygon = Polygon([Coord(tuple(point)) for point in original_polygon])  # type: ignore
    with pyinstrument.profile():
        reduced_polygon = reduce_polygon(original_polygon, epsilon=1e-6)
