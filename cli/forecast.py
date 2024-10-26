"""Forecasting"""

from datetime import datetime, timedelta, UTC
from typing_extensions import Annotated

import typer
import pandas as pd

from src.config.squirrel_conf import Config
from src.data.influxdb import get_gci_data, write_gci_forecast
from src.forecasting.gci import builtin_forecast_gci
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
    """Perform evaluation for different combinations of forecast
    and lookback days on historical data."""
    parameter_eval(
        forecast_days=range(1, fc_max + 1),
        lookback_range=range(1, lookback_max + 1),
        hourly=hourly,
    )


@app.command()
def to_influx():
    """Perform the forecast, as configured, similar to 'demo'
    and write the result into InfluxDB."""
    now = datetime.now(tz=UTC)
    start_point = now - timedelta(days=Config.get_lookback_days(), hours=1)
    gci_history = get_gci_data(start=start_point, stop=now)
    forecast = builtin_forecast_gci(
        gci_history,
        days=Config.get_forecast_days(),
        lookback=Config.get_lookback_days(),
    )
    write_gci_forecast(forecast=forecast)


@app.command()
def range_to_influx(
    start: Annotated[
        str,
        typer.Argument(
            help=(
                "Starting date for forecast. Provide as ISO format date "
                "string, e.g., 2023-01-03T00:00+00:00"
            )
        ),
    ],
    amount_days: Annotated[
        str,
        typer.Argument(
            help=("For how many days should the forecasting should be executed?")
        ),
    ],
    energy_zone: Annotated[
        str,
        typer.Argument(
            help="Name of energy zone, e.g. 'DE'. Make sure it exists in InfluxDB."
        ),
    ],
    forecast_days: Annotated[
        int,
        typer.Option(
            help="Forecast range in days. If None, defaults to configuration file."
        ),
    ] = None,
    lookback_days: Annotated[
        int,
        typer.Option(
            help="Amount of lookback days. If None, defaults to configuration file."
        ),
    ] = None,
):
    """Perform daily forecasts in a time range and write data
    into InfluxDB.
    """
    fc_dates = pd.date_range(
        start=datetime.fromisoformat(start),
        periods=amount_days,
        freq="d",
        tz="UTC",
    )
    if forecast_days is None:
        forecast_days = Config.get_forecast_days()
    if lookback_days is None:
        lookback_days = Config.get_lookback_days()
    influx_opt_hist = Config.get_influx_config()["gci"]["history"]
    influx_opt_fc = Config.get_influx_config()["gci"]["forecast"]
    influx_opt_hist.get("tags").update({"zone": energy_zone})
    influx_opt_fc.get("tags").update({"zone": energy_zone})
    for fc_date in fc_dates:
        gci_history = get_gci_data(
            start=fc_date - timedelta(days=lookback_days),
            stop=fc_date,
            options=influx_opt_hist,
        )
        forecast = builtin_forecast_gci(
            gci_history,
            days=forecast_days,
            lookback=lookback_days,
        )
        write_gci_forecast(forecast=forecast, options=influx_opt_fc)
