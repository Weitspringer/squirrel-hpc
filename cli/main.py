"""Command Line Interface"""

from datetime import datetime, UTC
from typing_extensions import Annotated

import typer

from cli import forecast, emaps, scenarios
from src.errors.scheduling import (
    NoSuitableNodeException,
    NoWindowAllocatedException,
    JobTooLongException,
)
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
        typer.Argument(help="""Other sbatch commands, e.g. "--priority=<value>"."""),
    ],
    runtime: Annotated[
        int,
        typer.Argument(help="Reserved amount of time (hours), e.g. '1'."),
    ],
    partition: Annotated[
        str,
        typer.Option(help="Comma separated list of partitions, e.g. 'gpu,cpu'."),
    ] = None,
    gpus_per_node: Annotated[
        str,
        typer.Option(help="Request one or more GPUs. Use this form: [type:]number."),
    ] = None,
):
    """Submit an sbatch job."""
    # Parse arguments
    partitions = partition.split(",") if partition is not None else None
    gpu_options = gpus_per_node.split(":")
    num_gpus = None
    gpu_name = None
    if len(gpu_options) == 2:
        gpu_name = gpu_options[0]
        num_gpus = int(gpu_options[1])
    elif len(gpu_options) == 1:
        try:
            num_gpus = int(gpu_options[0])
        except ValueError as _:
            print("GPU options should be given in this format: [type:]number")
            raise typer.Exit(1)
    else:
        print("GPU options should be given in this format: [type:]number")
        raise typer.Exit(1)
    # Schedule batch job
    try:
        submit_sbatch(command, runtime, partitions, num_gpus, gpu_name)
    except (
        NoWindowAllocatedException,
        NoSuitableNodeException,
        JobTooLongException,
    ) as e:
        print(e)
        raise typer.Exit(1)
    raise typer.Exit()


@app.command(rich_help_panel="Simulation")
def simulate_submit(
    command: Annotated[
        str,
        typer.Argument(help="""Other sbatch commands, e.g. "--priority=<value>"."""),
    ],
    runtime: Annotated[
        int,
        typer.Argument(help="Reserved amount of time (hours), e.g. '1'."),
    ],
    partition: Annotated[
        str,
        typer.Option(help="Comma separated list of partitions, e.g. 'gpu,cpu'."),
    ] = None,
    gpus_per_node: Annotated[
        str,
        typer.Option(help="Request one or more GPUs. Use this form: [type:]number."),
    ] = None,
    submit_date: Annotated[
        str,
        typer.Option(help="Submit date of the simulation."),
    ] = None,
):
    """Simulate submitting an sbatch job."""
    # Parse arguments
    partitions = partition.split(",") if partition is not None else None
    gpu_options = gpus_per_node.split(":")
    num_gpus = None
    gpu_name = None
    if len(gpu_options) == 2:
        gpu_name = gpu_options[0]
        num_gpus = int(gpu_options[1])
    elif len(gpu_options) == 1:
        try:
            num_gpus = int(gpu_options[0])
        except ValueError as _:
            print("GPU options should be given in this format: [type:]number")
            raise typer.Exit(1)
    else:
        print("GPU options should be given in this format: [type:]number")
        raise typer.Exit(code=1)
    # Determine submit date for simulation
    submit_date = (
        datetime.fromisoformat(submit_date)
        if submit_date is not None
        else datetime.now(tz=UTC)
    )
    # Submit batch job
    try:
        simulate_submit_sbatch(
            command, runtime, submit_date, partitions, num_gpus, gpu_name
        )
    except (
        NoWindowAllocatedException,
        NoSuitableNodeException,
        JobTooLongException,
    ) as e:
        print(e)
        raise typer.Exit(1)
    raise typer.Exit()
