"""Analyze data from internal datacenter."""

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from research.carbon_emmissions.energycharts import get_carbon_intensity
from research.energy_data.energycharts import fetch_public_power

########
# CALCULATIONS
########

# Get slurm job data for the node
node = "gx02"
country = "de"
slurm_file = Path("research") / "data" / "datalake" / "slurm.csv"
slurm_df = pd.read_csv(slurm_file)
slurm_df = slurm_df[slurm_df["Nodelist"] == node]
slurm_df["Start"] = pd.to_datetime(slurm_df["Start"])
slurm_df["End"] = pd.to_datetime(slurm_df["End"])
slurm_df["Duration"] = slurm_df["End"] - slurm_df["Start"]
slurm_df = slurm_df.sort_values(by="Start")
slurm_df = slurm_df[slurm_df["Duration"] >= pd.Timedelta(minutes=10)].reset_index()

# Get node power data
node_file = Path("research") / "data" / "datalake" / "power" / f"{node}.csv"
node_df = pd.read_csv(node_file)
node_df["Time"] = pd.to_datetime(node_df["Time"])
start_date = node_df["Time"].min()
end_date = node_df["Time"].max()
# Get node carbon emmissions
public_power = fetch_public_power(country=country, start=start_date, end=end_date)
carbon_intensities = get_carbon_intensity(country=country, response=public_power)

########
# PLOTTING
########

_, ax = plt.subplots(layout="tight")

##### POWER DATA
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

##### JOBS
twin = ax.twinx()
for index, job in slurm_df.iterrows():
    current_height = index + 1
    twin.hlines(
        y=current_height,
        xmin=job["Start"],
        xmax=job["End"],
        linewidth=2,
        alpha=0.8,
        color="C1",
    )
twin.set(ylabel="Job ID (Height represents individual jobs)")
twin.yaxis.label.set_color("C1")
twin.tick_params(axis="y", colors="C1")

##### CARBON INTENSITY
twin2 = ax.twinx()
ts = list(map(datetime.fromtimestamp, carbon_intensities["unix_seconds"]))
(p3,) = twin2.plot(
    ts, carbon_intensities["data"], color="black", alpha=0.3, label="Carbon Intensity"
)
twin2.set(ylabel="gCO2-eq./KWh")
twin2.yaxis.label.set_color("black")
twin2.tick_params(axis="y", colors="black")
twin2.spines["right"].set_position(("outward", 60))

##### MISC
plt.gcf().autofmt_xdate()
plt.title(f"Power consumption and jobs on node {node}")
ax.legend(handles=[p1, p3])
plt.show()
