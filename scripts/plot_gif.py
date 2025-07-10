"""Plot the loss curve for a test polygon."""

import numpy as np
import pickle, random
from polygenerator import random_polygon as _random_polygon  # type: ignore

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import TABLEAU_COLORS

from polyshell import reduce_polygon
from polyshell.geometry import Polygon, Coord


if __name__ == "__main__":

    random.seed(0)
    no_of_vertices = 50
    poly: list[tuple[float, float]] = _random_polygon(no_of_vertices)
    original_polygon = Polygon.from_array(list(reversed(poly)))

    # with open("./tests/data/ionian_polygon_points.pkl", "rb") as f:
    #     original_polygon = np.array(pickle.load(f))

    original_polygon = Polygon([Coord(tuple(point)) for point in original_polygon])  # type: ignore
    # reduced_polygon = reduce_polygon(original_polygon, epsilon=1e-1)

    # Extract data
    x_orig, y_orig = zip(*original_polygon, original_polygon[0])
    # x_reduced, y_reduced = zip(*reduced_polygon)

    # Plot original and reduced polygons
    # plt.plot(x_orig, y_orig, "b-")
    # plt.plot(x_reduced, y_reduced, "r-")

    fig, ax = plt.subplots()
    ax.plot(x_orig, y_orig, "k--", lw=1.25)
    line, = ax.plot([], [], 'b-', lw=2)
    ax.set_xlim(0, 1.)
    ax.set_ylim(0., 1.)

    def init():
        line.set_data([], [])
        return line,

    def update(i):
        reduced_polygon = reduce_polygon(original_polygon, i, epsilon=1e-1)

        # Extract data
        x, y = zip(*reduced_polygon)
        line.set_data(x, y)
        return line,

    # frames = list(reversed(range(20)))

    ani = animation.FuncAnimation(
        fig, update, frames=no_of_vertices, init_func=init,
        blit=True, interval=300, repeat=True
    )
    ani.save('animation.mp4', writer='ffmpeg')
    # ani.save('animation.gif', writer='pillow')

    plt.show()
