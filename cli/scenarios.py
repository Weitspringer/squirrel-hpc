"""Big simulations of scenarios."""

import enum
from pathlib import Path
from typing_extensions import Annotated

import typer

from src.config.squirrel_conf import Config
from src.sim.common.pipeline import plot_year_gci
from src.sim.temporal import (
    ascending,
    constant,
    descending,
    forecast,
    chronus,
)
from src.sim.spatial import fifo as spat_fifo, temporal as spat_temp
from src.sim.spatiotemporal import temporal as spattemp_temp

app = typer.Typer()
ZONES = [
    {"name": "IS", "utc_shift_hours": +0},
    {"name": "IN-WE", "utc_shift_hours": +5.5},
    {"name": "NO", "utc_shift_hours": +2},
    {"name": "AU-NSW", "utc_shift_hours": +11},
    {"name": "DE", "utc_shift_hours": +1},
]


class TemporalEnum(enum.Enum):
    """Options for temporal shifting scenarios."""

    ASC = "asc"
    CONS = "cons"
    DESC = "desc"
    FC = "desc+forecast"
    CHRON = "chronus"


class SpatialEnum(enum.Enum):
    """Options for spatial shifting scenarios."""

    FIFO = "vs-fifo"
    TEMP = "vs-temporal"


class SpatiotemporalEnum(enum.Enum):
    """Options for spatiotemporal shifting scenarios."""

    TEMP = "vs-temporal"


@app.command()
def temporal(
    scenario: Annotated[TemporalEnum, typer.Argument(help="Target scenario.")],
):
    """Run scenario which evaluates temporal shifting."""
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
    scenario: Annotated[SpatialEnum, typer.Argument(help="Target scenario.")],
):
    """Run scenario which evaluates spatial shifting."""
    sc = scenario.value
    if sc == SpatialEnum.FIFO.value:
        spat_fifo.run()
    elif sc == SpatialEnum.TEMP.value:
        spat_temp.run()


@app.command()
def spatiotemporal(
    scenario: Annotated[SpatiotemporalEnum, typer.Argument(help="Target scenario.")],
):
    """Run scenario which evaluates spatiotemporal shifting."""
    sc = scenario.value
    if sc == SpatialEnum.TEMP.value:
        spattemp_temp.run()


@app.command()
def visualize():
    """Visualize results for available scenario results."""
    scenarios = [
        ascending,
        constant,
        descending,
        forecast,
        chronus,
        spat_fifo,
        spat_temp,
        spattemp_temp,
    ]
    for sc in scenarios:
        if Path(sc.RESULT_DIR / "data" / "results.csv").exists():
            sc.visualize()
    plot_year_gci(
        year="2023",
        zones_dict=ZONES,
        save_path=Config.get_local_paths()["viz_path"]
        / "misc"
        / "gci_average_zones.pdf",
    )
