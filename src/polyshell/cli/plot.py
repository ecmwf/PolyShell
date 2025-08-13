from pathlib import Path

import numpy as np
import numpy.typing as npt
import typer
from matplotlib import pyplot as plt
from scipy.stats import linregress

from polyshell import reduce_polygon
from polyshell.cli.utils import load_from_path
from polyshell.convex_hull import melkman

app = typer.Typer()


def adaptive_step(
    eps: npt.NDArray[np.float64], length: npt.NDArray[np.int64], min_length: int, gamma: float = -1.0
) -> any:
    """Predict an adaptive step size based on past data."""
    fit = linregress(eps, (length - min_length)**gamma)

    return fit


# TODO: Write a func which selects and adaptive epsilon based on reduction rate


@app.command()
def loss_curve(input_path: Path, startup_step: float = 1e-6, startup_count: int = 100):
    """Plot the loss curve."""
    poly = load_from_path(input_path)
    min_len = len(melkman(poly))
    print(f"{min_len} / {len(poly)}")

    gamma = -1.65

    # Start-up
    startup_eps = startup_step * np.arange(1, startup_count + 1)
    startup_len: list[int] = []
    for eps in startup_eps:
        poly = reduce_polygon(poly, eps)
        startup_len.append(len(poly))
    startup_len = np.array(startup_len)
    fit = adaptive_step(startup_eps, startup_len, min_len, gamma=gamma)

    # plt.plot(startup_eps, (startup_len - min_len)**gamma)
    # plt.xlabel("Epsilon")
    # plt.ylabel(f"(No. points - No. hull points)^{gamma:.2f}")
    # plt.show()
    # assert False

    # a eps + b = (L - l)**gamma

    # Adaptive step
    pred_len = np.linspace(min_len, len(poly), 100)[1::][::-1]
    eps_vals = ((pred_len - min_len)**gamma - fit.intercept) / fit.slope

    poly_len: list[int] = []
    for eps in eps_vals:
        poly = reduce_polygon(poly, eps)
        poly_len.append(len(poly))

    plt.plot(eps_vals, poly_len, label="Loss")
    plt.plot(eps_vals, pred_len, label="Predicted")
    plt.xlabel("Epsilon")
    plt.ylabel("Count")
    plt.legend()
    plt.show()


@app.callback(invoke_without_command=True)
def plot(input_path: Path):
    """Plot a polygon from an input file."""
    poly = load_from_path(input_path)
    x, y = zip(*poly)
    # plt.plot(x, y)
    # plt.show()
