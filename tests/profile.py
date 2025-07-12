"""Run a profiler on a test polygon."""

import pickle

import pyinstrument
from polyshell import reduce_polygon

if __name__ == "__main__":
    with open("./tests/data/ionian_polygon_points.pkl", "rb") as f:
        original_polygon = pickle.load(f)

    with pyinstrument.profile():
        reduce_polygon(original_polygon, epsilon=1e6)  # reduce to completion
