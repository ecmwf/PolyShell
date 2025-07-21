"""Plot a polygon and its reduction."""

import pickle

import matplotlib.pyplot as plt
import numpy as np

from polyshell import reduce_polygon
from polyshell.geometry import Coord, Polygon

if __name__ == "__main__":
    with open("./tests/data/sea/ionian_sea.pkl", "rb") as f:
        original_polygon = np.array(pickle.load(f))

    original_polygon = Polygon([Coord(tuple(point)) for point in original_polygon])  # type: ignore
    reduced_polygon = reduce_polygon(original_polygon, epsilon=1e-6)

    # Extract data
    x_orig, y_orig = zip(*original_polygon)
    x_reduced, y_reduced = zip(*reduced_polygon)

    # Plot original and reduced polygons
    plt.plot(x_orig, y_orig, "b-")
    plt.plot(x_reduced, y_reduced, "r-")
    plt.show()
