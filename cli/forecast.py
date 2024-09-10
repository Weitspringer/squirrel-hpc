"""Forecasting"""

from typing_extensions import Annotated

import typer

from src.config.squirrel_conf import Config
from src.sim.forecasting.showcase import (
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
def simulation(
    hourly: Annotated[
        bool,
        typer.Option(help="Simlulate hourly forecasts."),
    ] = False,
):
    """Generate a series of forecasts on historial data."""
    visualize_simulation(
        forecast_days=Config.get_forecast_days(),
        lookback_days=Config.get_lookback_days(),
        hourly=hourly,
    )


@app.command()
def param(
    fc_max: Annotated[
        int,
        typer.Option(
            help="Max. number of days for which a forecast is generated (min. 1)."
        ),
    ] = 3,
    lookback_max: Annotated[
        int,
        typer.Option(help="Max. number of days looked back when forecasting (min. 1)."),
    ] = 10,
    hourly: Annotated[
        bool,
        typer.Option(help="Simlulate hourly forecasts."),
    ] = False,
):
    """Perform evaluation for different combinations of forecast and lookback days on historical data."""
    parameter_eval(
        forecast_days=range(1, fc_max + 1),
        lookback_range=range(1, lookback_max + 1),
        hourly=hourly,
    )
