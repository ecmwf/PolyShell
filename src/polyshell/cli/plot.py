from pathlib import Path

import typer
from matplotlib import pyplot as plt

from polyshell.cli.utils import load_from_path

app = typer.Typer()


@app.callback(invoke_without_command=True)
def plot(input_path: Path):
    """Plot a polygon from an input file."""
    poly = load_from_path(input_path)
    x, y = zip(*poly)
    plt.plot(x, y)
    plt.show()
