"""
Timeshifting Experiment: Carbon-Aware Scheduling vs. FIFO
+ Custom Forecasting

This experiment investigates job scheduling on a single-node cluster ("c1") to compare two scheduling strategies:
1. Carbon-Agnostic FIFO (First-In-First-Out)
2. Temporal Shifting based on grid lifecycle emissions.

**Experiment Setup:**
- 5 jobs are submitted sequentially, each requiring 1 hour to complete.
- The jobs have decreasing power demands (wattage) on node "c1":
  - Job 1: 250W
  - Job 2: 200W
  - Job 3: 150W
  - Job 4: 100W
  - Job 5: 50W
- The aim is to evaluate the environmental impact of the two scheduling strategies in terms of grid carbon emissions.

**Global Grid Zones Analyzed:**
- Germany (DE)
- France (FR)
- Great Britain (GB)
- Poland (PL)
- US-MIDA-PJM

**Methodology:**
- Schedulers have access to forecasted grid carbon intensity data for each zone, based on the values from the last 48 hours.
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

from src.sim.common.pipeline import main

# Experiment configuration
ZONES = ["IS", "IN-WE", "NO", "AU-NSW", "DE"]
START = "2023-01-03T00:00:00+00:00"
DAYS = 362
JOBS = {
    "job1": {"c1": 250},
    "job2": {"c1": 200},
    "job3": {"c1": 150},
    "job4": {"c1": 100},
    "job5": {"c1": 50},
}
LOOKAHEAD_HOURS = 24
CLUSTER_PATH = Path("src") / "sim" / "data" / "single-node-cluster.json"
RESULT_DIR = Config.get_local_paths()["viz_path"] / "scenarios" / "exp1" / "forecast"


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
        forecasting=True,
    )
