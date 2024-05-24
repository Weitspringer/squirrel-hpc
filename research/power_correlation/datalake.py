"""Analyze data from internal datacenter."""

from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _slurm_analysis(start_time: datetime, end_time: datetime, node: str):

    slurm_file = Path("research") / "data" / "datalake" / "slurm.csv"
    slurm_df = pd.read_csv(slurm_file)
    slurm_df = slurm_df[slurm_df["Nodelist"] == node]
    slurm_df["Start"] = pd.to_datetime(slurm_df["Start"])
    slurm_df["End"] = pd.to_datetime(slurm_df["End"])
    time_array = np.arange(start_time, end_time, timedelta(minutes=1)).astype(datetime)
    active_jobs = [0] * len(time_array)
    for index, _ in enumerate(active_jobs.copy()):
        ts = time_array[index]
        active_jobs[index] = (
            slurm_df[(slurm_df["Start"] <= ts)].shape[0]
            - slurm_df[(slurm_df["End"] <= ts)].shape[0]
        )

    plt.plot(time_array, active_jobs)
    plt.gcf().autofmt_xdate()
    plt.title(f"Number of Jobs on node {node}")
    plt.ylabel("# jobs")
    plt.show()


if __name__ == "__main__":
    NOW = datetime.now()
    _slurm_analysis(start_time=NOW - timedelta(days=7), end_time=NOW, node="gx02")
