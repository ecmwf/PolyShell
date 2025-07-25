"""Plot a polygon and its reduction."""

import pickle

import matplotlib.pyplot as plt

from polyshell import reduce_polygon
from polyshell.geometry import Polygon

if __name__ == "__main__":
    with open("./tests/data/sea/ionian_sea.pkl", "rb") as f:
        original_polygon = Polygon.from_array(pickle.load(f))

    reduced_polygon = reduce_polygon(original_polygon, epsilon=1e-6)

    # Extract data
    x_orig, y_orig = zip(*original_polygon)
    x_reduced, y_reduced = zip(*reduced_polygon)

    # Plot original and reduced polygons
    plt.plot(x_orig, y_orig, "b-")
    plt.plot(x_reduced, y_reduced, "r-")
    plt.show()
