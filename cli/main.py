"""Command Line Interface"""

from typing_extensions import Annotated

import typer

from cli import forecast
from src.submit.sbatch import submit_sbatch, simulate_submit_sbatch

app = typer.Typer()

app.add_typer(forecast.app, name="forecast")


@app.command()
def submit(
    command: Annotated[
        str,
        typer.Argument(help="Rest of the command"),
    ],
    runtime: Annotated[
        int,
        typer.Argument(help="Reserved amount of time (hours)."),
    ],
):
    """Submit an sbatch job."""
    submit_sbatch(command, runtime)


@app.command()
def simulate_submit(
    command: Annotated[
        str,
        typer.Argument(help="Rest of the command"),
    ],
    runtime: Annotated[
        int,
        typer.Argument(help="Reserved amount of time (hours)."),
    ],
    submit_date: Annotated[
        str,
        typer.Option(help="Submit date of the simulation."),
    ] = None,
):
    """Simulate submitting an sbatch job."""
    simulate_submit_sbatch(command, runtime, submit_date)
