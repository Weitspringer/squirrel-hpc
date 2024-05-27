"""Analyze data from internal datacenter."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def _slurm_analysis(node: str):
    # Get slurm job data for the node
    slurm_file = Path("research") / "data" / "datalake" / "slurm.csv"
    slurm_df = pd.read_csv(slurm_file)
    slurm_df = slurm_df[slurm_df["Nodelist"] == node]
    slurm_df["Start"] = pd.to_datetime(slurm_df["Start"])
    slurm_df["End"] = pd.to_datetime(slurm_df["End"])
    slurm_df["Duration"] = slurm_df["End"] - slurm_df["Start"]
    slurm_df = slurm_df[slurm_df["Duration"] >= pd.Timedelta(minutes=10)]
    slurm_df = slurm_df.reset_index().sort_values(by="Start")

    # Get node power data
    node_file = Path("research") / "data" / "datalake" / "power" / f"{node}.csv"
    node_df = pd.read_csv(node_file)
    node_df["Time"] = pd.to_datetime(node_df["Time"])

    _, ax = plt.subplots()
    # Plot power data
    (p1,) = ax.plot(
        node_df["Time"],
        node_df["Power Consumption [W]"],
        color="C0",
        alpha=0.5,
        label="Power consumption",
    )
    ax.set(ylabel="Power consumption [W]", xlabel="Time")
    ax.yaxis.label.set_color(p1.get_color())
    ax.tick_params(axis="y", colors=p1.get_color())

    # Plot each job on its own unique height
    twin = ax.twinx()
    for index, job in slurm_df.iterrows():
        current_height = index + 1
        twin.hlines(
            y=current_height,
            xmin=job["Start"],
            xmax=job["End"],
            linewidth=3,
            alpha=0.8,
            color="C1",
        )
    twin.set(ylabel="Job ID (Height represents individual jobs)")
    twin.yaxis.label.set_color("C1")
    twin.tick_params(axis="y", colors="C1")

    plt.gcf().autofmt_xdate()
    plt.title(f"Power consumption and jobs on node {node}")
    ax.legend(handles=[p1])
    plt.show()


if __name__ == "__main__":
    _slurm_analysis(node="gx02")
