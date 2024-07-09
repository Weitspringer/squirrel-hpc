"""Command Line Interface"""

import typer

from cli import forecast

app = typer.Typer()

app.add_typer(forecast.app, name="forecast")
