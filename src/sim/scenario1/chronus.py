"""
Timeshifting Experiment: Carbon-Aware Scheduling vs. Energy-Efficient Job Execution
"""

from pathlib import Path

from src.config.squirrel_conf import Config
from src.sched.scheduler import CarbonAgnosticFifo, TemporalShifting

from src.sim.common.pipeline import main, plot

# Experiment configuration
ZONES = ["IS", "IN-WE", "NO", "AU-NSW", "DE"]
START = "2023-01-01T00:00:00+00:00"
DAYS = 364
LOOKAHEAD_HOURS = 24
CLUSTER_PATH = Path("src") / "sim" / "data" / "single-node-cluster.json"
RESULT_DIR = (
    Config.get_local_paths()["viz_path"] / "scenarios" / "scenario1" / "chronus"
)


def run():
    """Run this scenario."""
    jobs_1 = {
        "job1": {"c01": 89},
    }
    jobs_2 = {
        "job1": {"c01": 100},
    }
    main(
        zones=ZONES,
        start=START,
        days=DAYS,
        lookahead_hours=LOOKAHEAD_HOURS,
        jobs_1=jobs_1,
        jobs_2=jobs_2,
        cluster_path=CLUSTER_PATH,
        result_dir=RESULT_DIR,
        strat_1=CarbonAgnosticFifo(),
        strat_2=TemporalShifting(),
        forecasting=False,
    )


def visualize():
    """Plot the results."""
    plot(days=DAYS, result_dir=RESULT_DIR)
