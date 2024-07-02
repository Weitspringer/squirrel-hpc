"""Command Line Interface"""

import typer

app = typer.Typer()


@app.command()
def hello(name: str):
    print(f"Hello {name}")


@app.command()
def forecast():
    print("Forecast!")
