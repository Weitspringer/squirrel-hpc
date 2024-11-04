"""Analyze data from internal datacenter."""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

########
# CALCULATIONS
########

# Get slurm job data for the node
node = "gx02"
country = "de"
root_folder = Path("scripts") / "data"
slurm_file = root_folder / "jobs.csv"
slurm_df = pd.read_csv(slurm_file)
slurm_df = slurm_df[
    (slurm_df["Nodelist"] == node) & (slurm_df["Name"] != "interactive")
]
slurm_df["Start"] = pd.to_datetime(slurm_df["Start"])
slurm_df["End"] = pd.to_datetime(slurm_df["End"])
slurm_df["Duration"] = slurm_df["End"] - slurm_df["Start"]
slurm_df = slurm_df.sort_values(by="Start")
slurm_df_filtered = slurm_df[
    slurm_df["Duration"] >= pd.Timedelta(minutes=1)
].reset_index()

# Get node power data
node_file = root_folder / f"{node}power.csv"
node_df = pd.read_csv(node_file)
node_df["time"] = pd.to_datetime(node_df["time"])
start_date = node_df["time"].min()
end_date = node_df["time"].max()

########
# PLOTTING
########

_, ax = plt.subplots()

##### POWER DATA
max_t = node_df["time"].max()
min_t = node_df["time"].min()
(p1,) = ax.plot(
    node_df["time"].iloc[::2],
    node_df["watts"].iloc[::2],
    color="tab:blue",
    linewidth=2,
    alpha=0.7,
    label="Power Draw",
)
ax.set(ylabel="Power Draw [W]", xlabel="Time")
ax.yaxis.label.set_color(p1.get_color())
ax.tick_params(axis="y", colors=p1.get_color())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H"))

##### JOBS
twin = ax.twinx()
for index, job in slurm_df_filtered.iterrows():
    current_height = index + 1
    twin.hlines(
        y=current_height,
        xmin=job["Start"],
        xmax=job["End"],
        linewidth=5,
        alpha=0.8,
        color="tab:orange",
        zorder=-100,
    )
twin.set(ylabel="Job ID")
twin.yaxis.label.set_color("tab:orange")
twin.tick_params(axis="y", colors="tab:orange")
twin.set_xlim(left=min_t, right=max_t)

##### MISC
plt.gcf().autofmt_xdate()
plt.title(f"Power Draw and Jobs on Node {node}")
plt.savefig(fname=root_folder / "analysis.pdf")
