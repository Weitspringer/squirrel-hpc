"""Command Line Interface"""

from datetime import datetime, UTC
from typing_extensions import Annotated

import typer

from cli import forecast, emaps, scenarios
from src.submit.sbatch import submit_sbatch, simulate_submit_sbatch

app = typer.Typer()

app.add_typer(
    forecast.app,
    name="forecast",
    help="Forecasting simulation.",
    rich_help_panel="Simulation",
)
app.add_typer(
    emaps.app,
    name="electricitymaps",
    help="Ingest data from Electricity Maps.",
    rich_help_panel="Data",
)
app.add_typer(
    scenarios.app,
    name="scenarios",
    help="Reproduce scenario results.",
    rich_help_panel="Simulation",
)


@app.command(rich_help_panel="Squirrel")
def submit(
    command: Annotated[
        str,
        typer.Argument(help="Rest of the command"),
    ],
    runtime: Annotated[
        int,
        typer.Argument(help="Reserved amount of time (hours)."),
    ],
    partition: Annotated[
        str,
        typer.Option(help="Comma separated list of partitions."),
    ] = None,
):
    """Submit an sbatch job."""
    partition = partition.split(",") if partition is not None else None
    submit_sbatch(command=command, runtime=runtime, partitions=partition)


@app.command(rich_help_panel="Simulation")
def simulate_submit(
    command: Annotated[
        str,
        typer.Argument(help="Rest of the command"),
    ],
    runtime: Annotated[
        int,
        typer.Argument(help="Reserved amount of time (hours)."),
    ],
    partition: Annotated[
        str,
        typer.Option(help="Comma separated list of partitions."),
    ] = None,
    submit_date: Annotated[
        str,
        typer.Option(help="Submit date of the simulation."),
    ] = None,
):
    """Simulate submitting an sbatch job."""
    partition = partition.split(",") if partition is not None else None
    submit_date = (
        datetime.fromisoformat(submit_date)
        if submit_date is not None
        else datetime.now(tz=UTC)
    )
    simulate_submit_sbatch(
        command=command, runtime=runtime, submit_date=submit_date, partitions=partition
    )
