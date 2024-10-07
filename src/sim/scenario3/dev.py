"""Spatiotemporal shifting experiment under test."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from tqdm import tqdm

from src.config.squirrel_conf import Config
from src.sched.scheduler import TemporalShifting, SpatiotemporalShifting

from src.sim.common.pipeline import main, plot

# Experiment configuration
ZONES = ["DE"]
START = "2023-08-01T00:00:00+00:00"
DAYS = 31
MAX_JOBS = 32
LOOKAHEAD_HOURS = 24
CLUSTER_PATH = Path("src") / "sim" / "data" / "multi-node-cluster.json"
RESULT_DIR = Config.get_local_paths()["viz_path"] / "scenarios" / "scenario3" / "test"

max_rel_savings_per_country = {}
for zone in ZONES:
    max_rel_savings_per_country.update({zone: []})
job_range = range(1, MAX_JOBS + 1)
jobs = {}
for i in tqdm(job_range):
    for j in range(i):
        jobs.update(
            {
                f"job{i}": {
                    "c1": 75,
                    "c12": 75,
                    "c2": 135,
                    "g1": 108,
                }
            }
        )
    main(
        zones=ZONES,
        start=START,
        days=DAYS,
        lookahead_hours=LOOKAHEAD_HOURS,
        jobs=jobs,
        cluster_path=CLUSTER_PATH,
        result_dir=RESULT_DIR,
        strat_1=TemporalShifting(),
        strat_2=SpatiotemporalShifting(),
        forecasting=False,
    )
    plot(days=DAYS, result_dir=RESULT_DIR)
    stats_df = pd.read_csv(RESULT_DIR / "data" / "stats.csv")
    for index, row in stats_df.iterrows():
        df_zon = stats_df.at[index, "zone"]
        max_rel_savings_per_country.get(df_zon).append(row["med_savings_rel"])

for zone, sav_data in max_rel_savings_per_country.items():
    plt.plot(
        job_range,
        sav_data,
        label=zone,
        linewidth=3,
        alpha=0.7,
    )
plt.ylabel("Median relative savings")
plt.xlabel("Amount of jobs")
plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=len(ZONES))
plt.grid(axis="y", linewidth=0.5)
plt.tight_layout()
plt.savefig(RESULT_DIR / "saturation.pdf")
plt.clf()
