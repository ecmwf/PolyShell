"""Plot the loss curve for a test polygon."""

import numpy as np
import pickle

import matplotlib.pyplot as plt
from matplotlib.colors import TABLEAU_COLORS

from polyshell.reducer import reduce_losses
from polyshell.geometry import Polygon, Coord


if __name__ == "__main__":
    with open("./tests/data/ionian_polygon_points.pkl", "rb") as f:
        original_polygon = np.array(pickle.load(f))

    polygon = Polygon([Coord(tuple(point)) for point in original_polygon])  # type: ignore
    reduced_segments = reduce_losses(polygon)

    color_list = list(TABLEAU_COLORS.values())

    # Iterate over segments and plot the losses
    for i, segment in enumerate(reduced_segments):
        point_range = range(len(segment))
        color = color_list[i % len(color_list)]

        plt.plot(point_range, np.cumsum(segment), "-", color=color)
        plt.plot(point_range, np.maximum.accumulate(segment), "--", color=color)

    # Fake a legend
    plt.plot([], [], "k-", label="Cumulative Loss")
    plt.plot([], [], "k--", label="Maximum Loss")

    plt.xlabel("Points removed")
    plt.ylabel("Loss")
    plt.legend()
    plt.show()
