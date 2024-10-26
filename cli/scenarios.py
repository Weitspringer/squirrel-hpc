"""Big simulations of scenarios."""

import enum
from pathlib import Path
from typing_extensions import Annotated

import typer

from src.sim.temporal import (
    ascending,
    constant,
    descending,
    forecast,
    chronus,
)
from src.sim.spatial import util_33

app = typer.Typer()


class TemporalEnum(enum.Enum):
    """Options for temporal shifting scenarios."""

    ASC = "asc"
    CONS = "cons"
    DESC = "desc"
    FC = "desc+forecast"
    CHRON = "chronus"


class SpatialEnum(enum.Enum):
    """Options for spatial shifting scenarios."""

    UTIL33 = "util_33"


@app.command()
def temporal(
    scenario: Annotated[TemporalEnum, typer.Argument(help="Target environment.")],
):
    """Run scenario which compares temporal shifting with carbon-agnostic FIFO."""
    sc = scenario.value
    if sc == TemporalEnum.ASC.value:
        ascending.run()
    elif sc == TemporalEnum.CONS.value:
        constant.run()
    elif sc == TemporalEnum.DESC.value:
        descending.run()
    elif sc == TemporalEnum.FC.value:
        forecast.run()
    elif sc == TemporalEnum.CHRON.value:
        chronus.run()


@app.command()
def spatial(
    scenario: Annotated[SpatialEnum, typer.Argument(help="Target environment.")],
):
    """Run scenario which compares spatial shifting with carbon-agnostic FIFO."""
    sc = scenario.value
    if sc == SpatialEnum.UTIL33.value:
        util_33.run()


@app.command()
def visualize():
    """Visualize results for available scenario results."""
    scenarios = [
        ascending,
        constant,
        descending,
        forecast,
        chronus,
        util_33,
    ]
    for sc in scenarios:
        if Path(sc.RESULT_DIR / "data" / "results.csv").exists():
            sc.visualize()
