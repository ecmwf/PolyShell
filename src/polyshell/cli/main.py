"""Command-line-interface for PolyShell."""

try:
    import typer
except ModuleNotFoundError:
    raise ModuleNotFoundError("Install cli extra to use the PolyShell CLI.")

from polyshell.cli.plot import app as plot_app
from polyshell.cli.reduce import app as reduce_app

app = typer.Typer()
app.add_typer(reduce_app, name="reduce")
app.add_typer(plot_app, name="plot")


def main():
    app()
