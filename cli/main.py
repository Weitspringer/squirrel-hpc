"""Command Line Interface"""

import typer

from cli import forecast
from src.submit.sbatch import submit_sbatch

app = typer.Typer()

app.add_typer(forecast.app, name="forecast")


@app.command()
def submit(command, runtime: int):
    """Submit a sbatch script to Slurm through Squirrel."""
    submit_sbatch(command, runtime)
