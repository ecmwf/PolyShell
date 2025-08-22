"""Run a profiler on a test polygon."""

import pickle

from polyshell import reduce_polygon
from polyshell.geometry import Polygon

import pyinstrument

if __name__ == "__main__":
    with open("./tests/data/sea/ionian_sea.pkl", "rb") as f:
        original_polygon = Polygon.from_array(pickle.load(f))

    with pyinstrument.profile():
        reduced_polygon = reduce_polygon(original_polygon, epsilon=1e-6)
