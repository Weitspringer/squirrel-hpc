"""Big simulations of scenarios."""

import enum
from pathlib import Path
from typing_extensions import Annotated

import typer

from src.sim.exp1 import ascending, constant, descending, forecast, multinode

app = typer.Typer()


class Exp1Enum(enum.Enum):
    """Options for experiment 1."""

    ASC = "asc"
    CONS = "cons"
    DESC = "desc"
    FC = "desc+forecast"
    MULTI = "cons+multi"


@app.command()
def timeshift(
    scenario: Annotated[Exp1Enum, typer.Argument(help="Target environment.")],
):
    """Compare timeshifting with carbon-agnostic FIFO."""
    sc = scenario.value
    if sc == Exp1Enum.ASC.value:
        ascending.run()
    elif sc == Exp1Enum.CONS.value:
        constant.run()
    elif sc == Exp1Enum.DESC.value:
        descending.run()
    elif sc == Exp1Enum.FC.value:
        forecast.run()
    elif sc == Exp1Enum.MULTI.value:
        multinode.run()
