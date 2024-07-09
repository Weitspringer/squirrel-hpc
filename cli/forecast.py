"""Forecasting"""

import typer
from typing_extensions import Annotated

from src.forecasting.showcase import (
    demo as fc_demo,
    parameter_eval,
    visualize_simulation,
)

app = typer.Typer()


@app.command()
def demo(forecast_days: int, lookback_days: int):
    """Get the live GCI forecast for a specified amount of days,
    using specified amount of lookback days."""
    fc_demo(forecast_days=forecast_days, lookback_days=lookback_days)


@app.command()
def simulation():
    """Generate a series of forecasts on historial data."""
    visualize_simulation()


@app.command()
def param(
    fc_max: Annotated[
        int,
        typer.Argument(
            help="Max. number of days for which a forecast is generated (min. 1)."
        ),
    ] = 3,
    lookback_max: Annotated[
        int,
        typer.Argument(
            help="Max. number of days looked back when forecasting (min. 2)."
        ),
    ] = 10,
):
    """Perform evaluation for different combinations of forecast and lookback days on historical data."""
    parameter_eval(
        forecast_days=range(1, fc_max + 1), lookback_range=range(2, lookback_max + 1)
    )
