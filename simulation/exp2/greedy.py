"""Spatial shifting experiment with greedy strategy."""

from pathlib import Path

from src.config.squirrel_conf import Config
from src.sched.scheduler import CarbonAgnosticFifo, SpatialGreedyShifting

from simulation.common.scheduling import main

# Experiment configuration
ZONES = ["DE", "FR", "GB", "PL", "US-MIDA-PJM"]
START = "2023-01-01T00:00:00+00:00"
DAYS = 364
JOBS = {
    "job1": {
        "c1": 50,
        "c12": 50,
        "c2": 60,
        "g1": 57,
    },
    "job2": {
        "c1": 50,
        "c12": 50,
        "c2": 60,
        "g1": 57,
    },
    "job3": {
        "c1": 50,
        "c12": 50,
        "c2": 60,
        "g1": 57,
    },
    "job4": {
        "c1": 50,
        "c12": 50,
        "c2": 60,
        "g1": 57,
    },
    "job5": {
        "c1": 50,
        "c12": 50,
        "c2": 60,
        "g1": 57,
    },
    "job6": {
        "c1": 50,
        "c12": 50,
        "c2": 60,
        "g1": 57,
    },
}
LOOKAHEAD_HOURS = 24
CLUSTER_PATH = Path("simulation") / "data" / "multi-node-cluster.json"
RESULT_DIR = Config.get_local_paths()["viz_path"] / "simulation" / "exp2" / "greedy"

main(
    zones=ZONES,
    start=START,
    days=DAYS,
    lookahead_hours=LOOKAHEAD_HOURS,
    jobs=JOBS,
    cluster_path=CLUSTER_PATH,
    result_dir=RESULT_DIR,
    strat_1=CarbonAgnosticFifo(),
    strat_2=SpatialGreedyShifting(),
    forecasting=True,
)
