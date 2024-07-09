"""Forecasting"""

import typer

from src.forecasting.showcase import _demo, _parameter_eval

app = typer.Typer()


@app.command()
def demo(forecast_days: int, lookback_days: int):
    _demo(forecast_days=forecast_days, lookback_days=lookback_days)


@app.command()
def param(forecast_range: list[int], lookback_range: list[int]):
    _parameter_eval(forecast_days=forecast_range, lookback_range=lookback_range)
