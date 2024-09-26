"""Spatial shifting experiment with loadbalancer strategy, 90% utilization on each node."""

from pathlib import Path

from src.config.squirrel_conf import Config
from src.sched.scheduler import CarbonAgnosticFifo, SpatialShifting

from src.sim.common.pipeline import main, plot

# Experiment configuration
ZONES = ["IS", "IN-WE", "NO", "AU-NSW", "DE"]
START = "2023-01-01T00:00:00+00:00"
DAYS = 364
JOBS = {}
for i in range(10):
    JOBS.update(
        {
            f"job{i}": {
                "c1": 112.5,
                "c12": 112.5,
                "c2": 202.5,
                "g1": 162,
            }
        }
    )
LOOKAHEAD_HOURS = 24
CLUSTER_PATH = Path("src") / "sim" / "data" / "multi-node-cluster.json"
RESULT_DIR = Config.get_local_paths()["viz_path"] / "scenarios" / "scenario2" / "lb_90"


def run():
    """Run this scenario."""
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


def visualize():
    """Plot the results."""
    plot(days=DAYS, result_dir=RESULT_DIR)
