"""Pipeline for comparison of two scheduling strategies."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config.squirrel_conf import Config

ZONES = ["IS", "IN-WE", "NO", "AU-NSW", "DE"]
constres = (
    Config.get_local_paths()["viz_path"]
    / "scenarios"
    / "temporal"
    / "constant"
    / "data"
)
ascres = (
    Config.get_local_paths()["viz_path"]
    / "scenarios"
    / "temporal"
    / "ascending"
    / "data"
)
descres = (
    Config.get_local_paths()["viz_path"]
    / "scenarios"
    / "temporal"
    / "descending"
    / "data"
)
res = Config.get_local_paths()["viz_path"] / "scenarios" / "scenario1" / "summary"
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

utilizations = ("Constant", "Ascending", "Descending")
# Constant watt usage
constres = pd.read_csv(constres / "stats.csv")
constres.set_index("zone", inplace=True)
# Increasing watt usage
ascres = pd.read_csv(ascres / "stats.csv")
ascres.set_index("zone", inplace=True)
# Decresing watt usage
descres = pd.read_csv(descres / "stats.csv")
descres.set_index("zone", inplace=True)

zoned_res = {}

for zone in ZONES:
    zoned_res.update(
        {
            zone: [
                constres.at[zone, "med_savings_rel"],
                ascres.at[zone, "med_savings_rel"],
                descres.at[zone, "med_savings_rel"],
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
plt.savefig(res / "scenario1.pdf")
