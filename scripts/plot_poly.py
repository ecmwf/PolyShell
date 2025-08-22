"""Plot a polygon and its reduction."""

import pickle

import matplotlib.pyplot as plt
import numpy as np

from polyshell import reduce_polygon
from polyshell.geometry import Polygon

if __name__ == "__main__":
    with open("./tests/data/sea/ionian_sea.pkl", "rb") as f:
        original_polygon = Polygon.from_array(pickle.load(f))

    reduced_polygon = reduce_polygon(original_polygon, epsilon=1e-3)

    # Extract data
    x_orig, y_orig = zip(*original_polygon)
    x_reduced, y_reduced = zip(*reduced_polygon)
    print(1. - len(x_reduced) / len(x_orig))

    # Define arrow tail and head coordinates
    end = (21.311, 37.665)
    start = (21.316, 37.675)

    # Plot original and reduced polygons
    plt.plot(x_orig, y_orig, "b-")
    plt.plot(x_reduced, y_reduced, "r-")
    # plt.annotate('', xy=end, xytext=start,
    #              arrowprops=dict(
    #                  arrowstyle='fancy',
    #                  color='black',
    #                  lw=2,
    #                  shrinkA=0, shrinkB=0,
    #                  mutation_scale=5
    #              ))
    # plt.annotate('', xy=end, xytext=start,
    #              arrowprops=dict(arrowstyle='->,head_length=1,head_width=0.5', color='black', lw=2))
    plt.xlim([21.1, 21.5])
    plt.ylim([38.25, 38.6])
    plt.show()
