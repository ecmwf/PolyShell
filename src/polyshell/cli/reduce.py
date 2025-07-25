from pathlib import Path

import typer

from polyshell.cli.utils import load_from_path, save_to_path

app = typer.Typer()


@app.callback(invoke_without_command=True)
def reduce(input_path: Path, output_path: Path):
    """Reduce a polygon from an input file."""
    poly = load_from_path(input_path)
    red_poly = ...
    save_to_path(red_poly, output_path)
