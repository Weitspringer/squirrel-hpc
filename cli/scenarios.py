"""Big simulations of scenarios."""

import enum
from pathlib import Path
from typing_extensions import Annotated

import typer

from src.config.squirrel_conf import Config
from src.sim.common.pipeline import plot_year_gci
from src.sim.temporal import (
    worst,
    constant,
    best,
    forecast,
    chronus,
)
from src.sim.spatial import (
    cpu_fifo as spat_cpu_fifo,
    cpu_temporal as spat_cpu_temp,
    cpu_greedy as spat_cpu_greedy,
    gpu_fifo as spat_gpu_fifo,
    gpu_temporal as spat_gpu_temp,
    gpu_greedy as spat_gpu_greedy,
)
from src.sim.spatiotemporal import (
    cpu_fifo as spattemp_cpu_fifo,
    cpu_temporal as spattemp_cpu_temp,
    cpu_spatial as spattemp_cpu_spat,
    gpu_fifo as spattemp_gpu_fifo,
    gpu_temporal as spattemp_gpu_temp,
    gpu_spatial as spattemp_gpu_spat,
)

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

    SIN = "single"
    CHRON = "chronus"


class SpatialEnum(enum.Enum):
    """Options for spatial shifting scenarios."""

    CPU = "cpu"
    GPU = "gpu"


class SpatiotemporalEnum(enum.Enum):
    """Options for spatiotemporal shifting scenarios."""

    CPU = "cpu"
    GPU = "gpu"


@app.command()
def temporal(
    scenario: Annotated[TemporalEnum, typer.Argument(help="Target scenario.")],
):
    """Run scenario which evaluates temporal shifting."""
    sc = scenario.value
    if sc == TemporalEnum.SIN.value:
        worst.run()
        constant.run()
        best.run()
        forecast.run()
    elif sc == TemporalEnum.CHRON.value:
        chronus.run()


@app.command()
def spatial(
    scenario: Annotated[SpatialEnum, typer.Argument(help="Target scenario.")],
):
    """Run scenario which evaluates spatial shifting."""
    sc = scenario.value
    if sc == SpatialEnum.CPU.value:
        spat_cpu_fifo.run()
        spat_cpu_greedy.run()
        spat_cpu_temp.run()
    elif sc == SpatialEnum.GPU.value:
        spat_gpu_fifo.run()
        spat_gpu_greedy.run()
        spat_gpu_temp.run()


@app.command()
def spatiotemporal(
    scenario: Annotated[SpatiotemporalEnum, typer.Argument(help="Target scenario.")],
):
    """Run scenario which evaluates spatiotemporal shifting."""
    sc = scenario.value
    if sc == SpatialEnum.CPU.value:
        spattemp_cpu_fifo.run()
        spattemp_cpu_temp.run()
        spattemp_cpu_spat.run()
    elif sc == SpatialEnum.GPU.value:
        spattemp_gpu_fifo.run()
        spattemp_gpu_temp.run()
        spattemp_gpu_spat.run()


@app.command()
def visualize():
    """Visualize results for available scenario results."""
    scenarios = [
        worst,
        constant,
        best,
        forecast,
        chronus,
        spat_cpu_fifo,
        spat_cpu_temp,
        spat_cpu_greedy,
        spat_gpu_fifo,
        spat_gpu_temp,
        spat_gpu_greedy,
        spattemp_cpu_fifo,
        spattemp_cpu_temp,
        spattemp_cpu_spat,
        spattemp_gpu_fifo,
        spattemp_gpu_temp,
        spattemp_gpu_spat,
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
