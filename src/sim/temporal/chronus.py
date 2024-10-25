"""
Temporal Shifting vs. Energy Efficiency

This experiment investigates job scheduling on a single-node cluster ("c1")
to compare two scheduling strategies:
1. Energy-optimized job with Carbon-Agnostic FIFO (First-In-First-Out).
2. Non-optimized job with Temporal Shifting based on (lifecycle) grid carbon intensity (GCI).

**Experiment Setup:**
- Based on measurements of a HPCG workload in related work (Chronus).
- 1 job is submitted.
- The job has the following power demands (wattage) on node "c1":
  - Job 1 (1 hour) : 59.56 W (energy-efficient with 11% energy savings)
  - Job 2 (1 hour) : 66.32 W (temporal shifting)
- The aim is to evaluate the environmental impact of the two scheduling strategies
in terms of emitted gCO2-eq.

**Global Grid Zones Analyzed:**
- Germany (DE) which has a very heterogeneous energy mix.
- Iceland (IS) with low average GCI and low variability.
- West India (IN-WE) with high average GCI and low variability.
- Norway (NO) with low average GCI and medium variability. 
- New South Wales, Australia (AUS-NSW) with high average GCI and medium variability.

**Methodology:**
- Schedulers have access to real-time grid carbon intensity data for each zone.
- Both scheduling approaches are able to schedule jobs within a 24-hour window.
- The experiment runs for every hour of the day using historical grid data from 2023.
- The analysis calculates:
  1. Median carbon savings of time-shifting scheduling compared to the FIFO approach,
     grouped by each hour of the day.
  2. Average job delay caused by the time-shifting strategy.

**Output:**
- Visualizations of the results, including hourly median carbon savings and job delays,
  are stored as PDF files in the designated output directory.
"""

from pathlib import Path

from src.config.squirrel_conf import Config
from src.sched.scheduler import CarbonAgnosticFifo, TemporalShifting

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
JOBS_1 = [
    JobSubmission(
        job_id="hpcg",
        partitions=["magic"],
        reserved_hours=1,
        num_gpus=None,
        gpu_name=None,
        power_draws={"cx01": [59.56]},
    )
]
JOBS_2 = [
    JobSubmission(
        job_id="hpcg",
        partitions=["magic"],
        reserved_hours=1,
        num_gpus=None,
        gpu_name=None,
        power_draws={"cx01": [66.32]},
    )
]
# What is the lookahead?
LOOKAHEAD_HOURS = 24
# Cluster configuration.
CLUSTER_PATH = Path("src") / "sim" / "data" / "single-node-cluster.json"
# TDP configuration.
TDP_PATH = Path("src") / "sim" / "data" / "single-node-tdp.cfg"
# Define where results will be stored.
RESULT_DIR = Config.get_local_paths()["viz_path"] / "scenarios" / "temporal" / "chronus"


### Experiment execution ###
def run():
    """Run this scenario."""
    main(
        zones=ZONES,
        start=START,
        days=DAYS,
        lookahead_hours=LOOKAHEAD_HOURS,
        jobs_1=JOBS_1,
        jobs_2=JOBS_2,
        cluster_path=CLUSTER_PATH,
        result_dir=RESULT_DIR,
        strat_1=CarbonAgnosticFifo(),
        strat_2=TemporalShifting(),
        forecasting=False,
    )


def visualize():
    """Plot the results."""
    plot(days=DAYS, result_dir=RESULT_DIR, zones_dict=ZONES, rel_ylim=(-12, 50))