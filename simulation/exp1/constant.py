"""Timeshifting experiment."""

from pathlib import Path

from src.config.squirrel_conf import Config
from src.sched.scheduler import CarbonAgnosticFifo, TemporalShifting

from simulation.common.scheduling import main

# Experiment configuration
ZONES = ["DE", "FR", "GB", "PL", "US-MIDA-PJM"]
START = "2023-08-01T00:00:00+00:00"
DAYS = 10
JOBS = {
    "job1": {"c1": 150},
    "job2": {"c1": 150},
    "job3": {"c1": 150},
    "job4": {"c1": 150},
    "job5": {"c1": 150},
}
LOOKAHEAD_HOURS = 24
CLUSTER_PATH = Path("simulation") / "data" / "single-node-cluster.json"
RESULT_DIR = Config.get_local_paths()["viz_path"] / "simulation" / "exp1" / "constant"

main(
    zones=ZONES,
    start=START,
    days=DAYS,
    lookahead_hours=LOOKAHEAD_HOURS,
    jobs=JOBS,
    cluster_path=CLUSTER_PATH,
    result_dir=RESULT_DIR,
    strat_1=CarbonAgnosticFifo(),
    strat_2=TemporalShifting(),
    forecasting=False,
)
