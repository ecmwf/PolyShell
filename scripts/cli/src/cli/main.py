import pickle
from pathlib import Path

import typer
from matplotlib import pyplot as plt

from polyshell import *

app = typer.Typer(no_args_is_help=True)


@app.command()
def plot_reduction(
    path: Path, mode: ReductionMode, val: float, method: ReductionMethod
):
    """Plot a polygon and its reduction."""
    with open(path, "rb") as f:
        original_poly = pickle.load(f)

    reduced_poly = reduce_polygon(original_poly, mode, val, method)

    # Report reduction
    print(f"Reduction rate: {len(reduced_poly)} / {len(original_poly)}")

    # Extract data
    x_orig, y_orig = zip(*original_poly)
    x_reduced, y_reduced = zip(*reduced_poly)

    # Plot original and reduced polygons
    plt.plot(x_orig, y_orig, "b-")
    plt.plot(x_reduced, y_reduced, "r-")
    plt.show()


if __name__ == "__main__":
    app()
