"""
Temporal Shifting vs. FIFO (+ Forecast Error)
"""

from pathlib import Path

from src.config.squirrel_conf import Config
from src.sched.scheduler import CarbonAgnosticFifo, TemporalShifting

from src.sim.common.pipeline import main, plot, JobSubmission

### Experiment configuration ###
# What is the PUE of the data center?
PUE = 1.4
# Define energy zones for simulation
ZONES = [
    {"name": "IS", "utc_shift_hours": +0},
    {"name": "IN-WE", "utc_shift_hours": +5.5},
    {"name": "NO", "utc_shift_hours": +2},
    {"name": "AU-NSW", "utc_shift_hours": +10},
    {"name": "DE", "utc_shift_hours": +2},
]
# When does the scheduling take place first?
START = "2023-01-04T23:00:00+00:00"
# Schedules are calculated hourly. For how many days?
DAYS = 360
# Define workloads which need to be scheduled for each iteration.
JOBS = [
    JobSubmission(
        job_id="tpcxai-sf3_[0]",
        partitions=["magic"],
        reserved_hours=2,
        num_gpus=None,
        gpu_name=None,
        power_draws={"cx01": [113.15, 7.87]},
    ),
    JobSubmission(
        job_id="tpcxai-sf3_[1]",
        partitions=["magic"],
        reserved_hours=2,
        num_gpus=None,
        gpu_name=None,
        power_draws={"cx01": [113.15, 7.87]},
    ),
    JobSubmission(
        job_id="tpcxai-sf10-no8_[0]",
        partitions=["magic"],
        reserved_hours=1,
        num_gpus=None,
        gpu_name=None,
        power_draws={"cx01": [100.31]},
    ),
    JobSubmission(
        job_id="tpcxai-sf10-no8_[1]",
        partitions=["magic"],
        reserved_hours=1,
        num_gpus=None,
        gpu_name=None,
        power_draws={"cx01": [100.31]},
    ),
    JobSubmission(
        job_id="tpcxai-sf1_[0]",
        partitions=["magic"],
        reserved_hours=1,
        num_gpus=None,
        gpu_name=None,
        power_draws={"cx01": [66.32]},
    ),
    JobSubmission(
        job_id="tpcxai-sf1_[1]",
        partitions=["magic"],
        reserved_hours=1,
        num_gpus=None,
        gpu_name=None,
        power_draws={"cx01": [66.32]},
    ),
]
# What is the lookahead?
LOOKAHEAD_HOURS = 24
# Cluster configuration.
CLUSTER_PATH = Path("src") / "sim" / "data" / "single-node-cluster.json"
# TDP configuration.
TDP_PATH = Path("src") / "sim" / "data" / "single-node-tdp.cfg"
# Define where results will be stored.
RESULT_DIR = (
    Config.get_local_paths()["viz_path"] / "scenarios" / "temporal" / "forecast"
)


### Experiment execution ###
def run():
    """Run this scenario."""
    main(
        pue=PUE,
        zones=ZONES,
        start=START,
        days=DAYS,
        lookahead_hours=LOOKAHEAD_HOURS,
        jobs_1=JOBS,
        jobs_2=JOBS,
        cluster_path=CLUSTER_PATH,
        result_dir=RESULT_DIR,
        strat_1=CarbonAgnosticFifo(),
        strat_2=TemporalShifting(),
        forecasting=True,
    )


def visualize():
    """Plot the results."""
    plot(days=DAYS, result_dir=RESULT_DIR, zones_dict=ZONES)
