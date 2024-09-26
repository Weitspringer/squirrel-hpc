"""Analyze statistical properties of GCI history from different zones."""

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config.squirrel_conf import Config
from src.data.influxdb import get_gci_data

ZONE_LABELS = {
    "AU-NSW": "Australia (New South Wales)",
    "CA-ON": "Canada (Ontario)",
    "CA-QC": "Canada (Québec)",
    "DE": "Germany",
    "DK": "Denmark",
    "FR": "France",
    "GB": "Great Britain",
    "IN-WE": "West India",
    "IS": "Iceland",
    "NL": "Netherlands",
    "NO": "Norway",
    "PL": "Poland",
    "SE": "Sweden",
    "SE-SE4": "South Sweden",
    "TW": "Taiwan",
    "US-MIDA-PJM": "USA (PJM)",
    "ZA": "South Africa",
}
YEAR = "2023"
RESULT_DIR = Path("viz") / "misc"
RESULT_DIR.mkdir(exist_ok=True, parents=True)
plt.style.use("seaborn-v0_8")


def analyze(zones: list[str]) -> None:
    cm = plt.get_cmap("tab20")
    ax = plt.gca()
    ax.set_prop_cycle(color=[cm(1.0 * i / len(zones)) for i in range(len(zones))])
    stats = []
    for zone in zones:
        start = datetime.fromisoformat(f"{YEAR}-01-01T00:00:00+00:00")
        end = datetime.fromisoformat(f"{YEAR}-12-31T23:59:59+00:00")
        influx_options = Config.get_influx_config()["gci"]["history"]
        influx_options.get("tags").update({"zone": zone})
        gci_hist = get_gci_data(start=start, stop=end, options=influx_options)
        gci_hist["Month"] = gci_hist["time"].apply(lambda x: x.month)
        gci_hist = gci_hist.set_index("time")
        avg_gci = np.average(gci_hist["gci"])
        cv = np.std(gci_hist["gci"]) / np.mean(gci_hist["gci"])
        plt.plot(avg_gci, cv, "o", label=ZONE_LABELS[zone])
        # Write stats
        stats.append(
            {
                "zone": zone,
                "gci_cv": cv,
                "gci_average": avg_gci,
                "num_points": len(gci_hist),
            }
        )
    plt.title("Properties of GCI time series in different zones, 2023")
    plt.xlabel("Average grid carbon intensity [gCO2-eq./kWh]")
    plt.ylabel("Coefficient of variation")
    plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    plt.tight_layout(pad=1)
    plt.savefig(RESULT_DIR / f"gci_in_zones.pdf")
    # Write stats
    stat_df = pd.DataFrame(stats)
    stat_df.set_index("zone", inplace=True)
    stat_df.to_csv(RESULT_DIR / f"gci_in_zones_stats.csv")


if __name__ == "__main__":
    analyze(ZONE_LABELS.keys())
