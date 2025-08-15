"""Plot a polygon and its reduction."""

import pickle

import matplotlib.pyplot as plt
import pyinstrument
from polyshell._polyshell import (
    reduce_polygon_char,
    reduce_polygon_rdp,
    reduce_polygon_vw,
)

if __name__ == "__main__":
    with open("./tests/data/sea/ionian_sea.pkl", "rb") as f:
        original_polygon = pickle.load(f)

    with pyinstrument.profile():
        reduced_polygon = reduce_polygon_vw(original_polygon, epsilon=1e-4)
        # reduced_polygon = reduce_polygon_rdp(original_polygon, epsilon=1e-2)
        # reduced_polygon = reduce_polygon_char(original_polygon, epsilon=4.28e-2)

    # Report reduction
    print(f"Reduction rate: {len(reduced_polygon)} / {len(original_polygon)}")

    # Extract data
    x_orig, y_orig = zip(*original_polygon)
    x_reduced, y_reduced = zip(*reduced_polygon)

    # Plot original and reduced polygons
    plt.plot(x_orig, y_orig, "b-")
    plt.plot(x_reduced, y_reduced, "r-")
    plt.show()
