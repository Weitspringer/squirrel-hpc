"""
Timeshifting Experiment: Carbon-Aware Scheduling vs. FIFO

This experiment investigates job scheduling on a single-node cluster ("c1") to compare two scheduling strategies:
1. Carbon-Agnostic FIFO (First-In-First-Out)
2. Temporal Shifting based on (lifecycle) grid carbon intensity (GCI).

**Experiment Setup:**
- 5 jobs are submitted sequentially, each requiring 1 hour to complete.
- The jobs have increasing power demands (wattage) on node "c1":
  - Job 1: 50W
  - Job 2: 100W
  - Job 3: 150W
  - Job 4: 200W
  - Job 5: 250W
- The aim is to evaluate the environmental impact of the two scheduling strategies in terms of grid carbon emissions.

**Global Grid Zones Analyzed:**
- Germany (DE) which has a very heterogeneous energy mix.
- Iceland (IS) with low average GCI and low variability.
- West India (IN-WE) with high average GCI and low variability.
- Norway (NO) with low average GCI and medium variability. 
- New South Wales, Australia (AUS-NSW) with high average GCI and medium variability.

**Methodology:**
- Schedulers have access to real-time grid carbon intensity data for each zone.
- Both scheduling approaches are able to schedule jobs within a 24-hour window, factoring in grid conditions.
- The experiment runs for every hour of the day using historical grid data from 2023.
- The analysis calculates:
  1. Median carbon savings of time-shifting scheduling compared to the FIFO approach, grouped by each hour of the day.
  2. Average job delay caused by the time-shifting strategy.

**Output:**
- Visualizations of the results, including hourly median carbon savings and job delays, are stored as PDF files in the designated output directory.
"""

from pathlib import Path

from src.config.squirrel_conf import Config
from src.sched.scheduler import CarbonAgnosticFifo, TemporalShifting

from src.sim.common.pipeline import main, plot

# Experiment configuration
ZONES = ["IS", "IN-WE", "NO", "AU-NSW", "DE"]
START = "2023-01-01T00:00:00+00:00"
DAYS = 364
JOBS = {
    "job1": {"c1": 50},
    "job2": {"c1": 100},
    "job3": {"c1": 150},
    "job4": {"c1": 200},
    "job5": {"c1": 250},
}
LOOKAHEAD_HOURS = 24
CLUSTER_PATH = Path("src") / "sim" / "data" / "single-node-cluster.json"
RESULT_DIR = Config.get_local_paths()["viz_path"] / "scenarios" / "exp1" / "ascending"


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
        strat_2=TemporalShifting(),
        forecasting=False,
    )


def visualize():
    """Plot the results."""
    plot(days=DAYS, result_dir=RESULT_DIR)
