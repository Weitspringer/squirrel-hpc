"""
Spatial Shifting vs. FIFO
"""

from pathlib import Path

from src.config.squirrel_conf import Config
from src.sched.scheduler import CarbonAgnosticFifo, SpatialShifting

from src.sim.common.pipeline import main, plot, JobSubmission

### Experiment configuration ###
# Define energy zones for simulation
ZONES = [
    {"name": "IS", "utc_shift_hours": +0},
    {"name": "IN-WE", "utc_shift_hours": +5.5},
    {"name": "NO", "utc_shift_hours": +2},
    {"name": "AU-NSW", "utc_shift_hours": +11},
    {"name": "DE", "utc_shift_hours": +1},
]
# When does the scheduling take place first?
START = "2022-12-31T23:00:00+00:00"
# Schedules are calculated hourly. For how many days?
DAYS = 364
# Define workloads which need to be scheduled for each iteration.
JOBS = [
    JobSubmission(
        job_id="tpcxai-sf1",
        partitions=["jinx"],
        reserved_hours=1,
        num_gpus=None,
        gpu_name=None,
        power_draws={
            "cx16": [128.94, 0],
            "cx17": [191.51, 70.87],
            "gx03": [119.78, 1.34],
        },
    ),
]
# What is the lookahead?
LOOKAHEAD_HOURS = 24
# Cluster configuration.
CLUSTER_PATH = Path("src") / "sim" / "data" / "3-node-cluster.json"
# TDP configuration.
TDP_PATH = Path("src") / "sim" / "data" / "3-node-tdp.cfg"
# Define where results will be stored.
RESULT_DIR = (
    Config.get_local_paths()["viz_path"] / "scenarios" / "temporal" / "single-job"
)


### Experiment execution ###
def run():
    """Run this scenario."""
    main(
        zones=ZONES,
        start=START,
        days=DAYS,
        lookahead_hours=LOOKAHEAD_HOURS,
        jobs_1=JOBS,
        jobs_2=JOBS,
        cluster_path=CLUSTER_PATH,
        result_dir=RESULT_DIR,
        strat_1=CarbonAgnosticFifo(),
        strat_2=SpatialShifting(),
        forecasting=False,
    )


def visualize():
    """Plot the results."""
    plot(days=DAYS, result_dir=RESULT_DIR, zones_dict=ZONES)
