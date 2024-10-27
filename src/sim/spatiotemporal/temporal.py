"""Spatiotemporal shifting experiment under test."""

from pathlib import Path

from matplotlib import ticker
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.optimize
from tqdm import tqdm

from src.config.squirrel_conf import Config
from src.sched.scheduler import TemporalShifting, SpatiotemporalShifting

from src.sim.common.pipeline import main, plot, JobSubmission

# Experiment configuration
# What is the PUE of the data center?
PUE = 1.4
ZONES = [{"name": "DE", "utc_shift_hours": +2}]
START = "2023-08-01T00:00:00+00:00"
DAYS = 1
MAX_JOBS = 12
LOOKAHEAD_HOURS = 24
CLUSTER_PATH = Path("src") / "sim" / "data" / "3-node-cluster.json"
META_PATH = Path("src") / "sim" / "data" / "3-node-meta.cfg"
RESULT_DIR = (
    Config.get_local_paths()["viz_path"]
    / "scenarios"
    / "spatiotemporal"
    / "vs-temporal"
)


def _exponential_func(x, a, b, c, d):
    return a * (b ** (x + c)) + d


### Experiment execution ###
def run():
    """Run this scenario."""
    max_rel_savings_per_country = {}
    for zone in ZONES:
        max_rel_savings_per_country.update({zone.get("name"): []})
    job_range = range(1, MAX_JOBS + 1)
    for i in tqdm(job_range):
        jobs = []
        for j in range(i):
            jobs.append(
                JobSubmission(
                    job_id=f"tpcxai-sf1_[{j}]",
                    partitions=["jinx"],
                    reserved_hours=2,
                    num_gpus=None,
                    gpu_name=None,
                    power_draws={
                        "cx16": [128.94, 0],
                        "cx17": [191.51, 70.87],
                        "gx03": [119.78, 1.34],
                    },
                )
            )
        main(
            pue=PUE,
            zones=ZONES,
            start=START,
            days=DAYS,
            lookahead_hours=LOOKAHEAD_HOURS,
            jobs_1=jobs,
            jobs_2=jobs,
            cluster_path=CLUSTER_PATH,
            result_dir=RESULT_DIR,
            strat_1=TemporalShifting(),
            strat_2=SpatiotemporalShifting(meta_path=META_PATH),
            forecasting=False,
        )
        plot(days=DAYS, result_dir=RESULT_DIR, zones_dict=ZONES)
        stats_df = pd.read_csv(RESULT_DIR / "data" / "stats.csv")
        for index, row in stats_df.iterrows():
            df_zon = stats_df.at[index, "zone"]
            max_rel_savings_per_country.get(df_zon).append(row["avg_savings_rel"])

    for zone, sav_data in max_rel_savings_per_country.items():
        popt, _ = scipy.optimize.curve_fit(_exponential_func, job_range, sav_data)
        utilization = [
            n_job * 0.02777777777777777777777777777778 for n_job in job_range
        ]
        plt.plot(
            utilization,
            _exponential_func(job_range, *popt),
            color="tab:red",
            label="Fitted Exponential Function",
            linewidth=2,
            alpha=0.7,
        )
        plt.gca().yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=0))
        plt.gca().xaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=0))
        plt.ylabel("Average g$\mathregular{CO_2}$-eq. Savings")
        plt.xlabel("Utilization")
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=len(ZONES))
        plt.grid(axis="y", linewidth=1, alpha=0.2)
        plt.grid(axis="x", linewidth=1, alpha=0.2)
        plt.ylim(0, 0.4)
        plt.tight_layout()
        plt.savefig(RESULT_DIR / "saturation.pdf")
        plt.clf()
        job_modulo_3 = ["1", "2", "0"]
        sav_data_aggr = list(np.reshape(sav_data, (4, 3)).mean(axis=0))
        plt.plot(job_modulo_3, sav_data_aggr)
        plt.gca().yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=0))
        plt.ylabel("Average g$\mathregular{CO_2}$-eq. Savings")
        plt.xlabel("Number of Jobs $mod$ Cluster Size")
        plt.ylim(0, 0.4)
        plt.grid(axis="y", linewidth=1, alpha=0.2)
        plt.tight_layout()
        plt.savefig(RESULT_DIR / "detail.pdf")


def visualize():
    """Plot the results."""
