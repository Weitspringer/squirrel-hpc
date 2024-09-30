"""Pipeline for comparison of two scheduling strategies."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config.squirrel_conf import Config

ZONES = ["IS", "IN-WE", "NO", "AU-NSW", "DE"]
lb30res = (
    Config.get_local_paths()["viz_path"] / "scenarios" / "scenario2" / "lb_30" / "data"
)
lb60res = (
    Config.get_local_paths()["viz_path"] / "scenarios" / "scenario2" / "lb_60" / "data"
)
lb90res = (
    Config.get_local_paths()["viz_path"] / "scenarios" / "scenario2" / "lb_90" / "data"
)
res = Config.get_local_paths()["viz_path"] / "scenarios" / "scenario2" / "summary"
res.mkdir(exist_ok=True, parents=True)

## Set unique colors for zones
if len(ZONES) <= 8:
    cm = plt.get_cmap("Set2")
elif len(ZONES) <= 10:
    cm = plt.get_cmap("tab10")
elif len(ZONES) <= 20:
    cm = plt.get_cmap("tab20")
else:
    cm = plt.get_cmap("hsv")
cmaplist = [cm(1.0 * i / len(ZONES)) for i in range(len(ZONES))]
zone_colors = {}
for idx, color in enumerate(cmaplist):
    zone_colors.update({ZONES[idx]: color})

small_size = 12
medium_size = 12
bigger_size = 12

plt.rc("font", size=small_size)  # controls default text sizes
plt.rc("axes", titlesize=small_size)  # fontsize of the axes title
plt.rc("axes", labelsize=medium_size)  # fontsize of the x and y labels
plt.rc("xtick", labelsize=small_size)  # fontsize of the tick labels
plt.rc("ytick", labelsize=small_size)  # fontsize of the tick labels
plt.rc("legend", fontsize=small_size)  # legend fontsize
plt.rc("figure", titlesize=bigger_size)  # fontsize of the figure title

utilizations = ("30% TDP", "60% TDP", "90% TDP")
# 30% utilization results
lb30 = pd.read_csv(lb30res / "stats.csv")
lb30.set_index("zone", inplace=True)
# 60% utilization results
lb60 = pd.read_csv(lb60res / "stats.csv")
lb60.set_index("zone", inplace=True)
# 90% utilization results
lb90 = pd.read_csv(lb90res / "stats.csv")
lb90.set_index("zone", inplace=True)

zoned_res = {}

for zone in ZONES:
    zoned_res.update(
        {
            zone: [
                lb30.at[zone, "med_savings_rel"],
                lb60.at[zone, "med_savings_rel"],
                lb90.at[zone, "med_savings_rel"],
            ]
        }
    )

x = np.arange(len(utilizations))
width = 0.175  # the width of the bars
multiplier = 0

fig, ax = plt.subplots()

for zone, measurement in zoned_res.items():
    offset = width * multiplier
    rects = ax.bar(
        x + offset, measurement, width, label=zone, color=zone_colors.get(zone)
    )
    multiplier += 1

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel("Median relative savings")
ax.set_xticks(x + (width * multiplier) / 2 - width / 2)
ax.set_xticklabels(utilizations)
plt.grid(axis="y", linewidth=0.5)
plt.ylim(0, 0.37)
plt.tight_layout()
plt.savefig(res / "spatial.pdf")
