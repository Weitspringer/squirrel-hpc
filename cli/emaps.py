"""Forecasting"""

from pathlib import Path
from typing_extensions import Annotated

import typer

from scripts.emaps_to_influx import ingest_emaps_history

app = typer.Typer()


@app.command()
def ingest_history(
    csv_path: Annotated[
        str,
        typer.Argument(help="Path to the csv file from Electricity Maps."),
    ],
):
    """Ingest historical data from Electricity Maps Data Portal."""
    ingest_emaps_history(Path(csv_path))
