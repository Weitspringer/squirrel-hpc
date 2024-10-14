"""Big simulations of scenarios."""

import enum
from pathlib import Path
from typing_extensions import Annotated

import typer

from src.sim.scenario1 import (
    ascending,
    constant,
    descending,
    forecast,
    multinode,
    chronus,
)
from src.sim.scenario2 import lb_30, lb_60, lb_90

app = typer.Typer()


class Scenario1Enum(enum.Enum):
    """Options for scenario 1."""

    ASC = "asc"
    CONS = "cons"
    DESC = "desc"
    FC = "desc+forecast"
    MULTI = "cons+multi"
    CHRON = "chronus"


class Scenario2Enum(enum.Enum):
    """Options for scenario 2."""

    LB30 = "lb-30"
    LB60 = "lb-60"
    LB90 = "lb-90"


@app.command()
def temporal(
    scenario: Annotated[Scenario1Enum, typer.Argument(help="Target environment.")],
):
    """Run scenario which compares temporal shifting with carbon-agnostic FIFO."""
    sc = scenario.value
    if sc == Scenario1Enum.ASC.value:
        ascending.run()
    elif sc == Scenario1Enum.CONS.value:
        constant.run()
    elif sc == Scenario1Enum.DESC.value:
        descending.run()
    elif sc == Scenario1Enum.FC.value:
        forecast.run()
    elif sc == Scenario1Enum.MULTI.value:
        multinode.run()
    elif sc == Scenario1Enum.CHRON.value:
        chronus.run()


@app.command()
def spatial(
    scenario: Annotated[Scenario2Enum, typer.Argument(help="Target environment.")],
):
    """Run scenario which compares spatial shifting with carbon-agnostic FIFO."""
    sc = scenario.value
    if sc == Scenario2Enum.LB30.value:
        lb_30.run()
    elif sc == Scenario2Enum.LB60.value:
        lb_60.run()
    elif sc == Scenario2Enum.LB90.value:
        lb_90.run()


@app.command()
def visualize():
    """Visualize results for available scenario results."""
    scenarios = [
        ascending,
        constant,
        descending,
        forecast,
        multinode,
        chronus,
        lb_30,
        lb_60,
        lb_90,
    ]
    for sc in scenarios:
        if Path(sc.RESULT_DIR / "data" / "results.csv").exists():
            sc.visualize()
