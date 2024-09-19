"""Spatial shifting experiment with greedy strategy."""

from pathlib import Path

from src.config.squirrel_conf import Config
from src.sched.scheduler import CarbonAgnosticFifo, SpatialShifting

from src.sim.common.pipeline import main

# Experiment configuration
ZONES = ["IS", "IN-WE", "NO", "AU-NSW", "DE"]
START = "2023-01-01T00:00:00+00:00"
DAYS = 364
JOBS = {}
for i in range(10):
    JOBS.update(
        {
            f"job{i}": {
                "c1": 50,
                "c12": 50,
                "c2": 65,
                "g1": 60,
            }
        }
    )
LOOKAHEAD_HOURS = 24
CLUSTER_PATH = Path("src") / "sim" / "data" / "multi-node-cluster.json"
RESULT_DIR = (
    Config.get_local_paths()["viz_path"] / "scenarios" / "exp2" / "loadbalancer"
)

main(
    zones=ZONES,
    start=START,
    days=DAYS,
    lookahead_hours=LOOKAHEAD_HOURS,
    jobs=JOBS,
    cluster_path=CLUSTER_PATH,
    result_dir=RESULT_DIR,
    strat_1=CarbonAgnosticFifo(),
    strat_2=SpatialShifting(),
    forecasting=False,
)
